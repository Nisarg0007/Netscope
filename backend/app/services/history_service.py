import threading
import time
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import delete
from app.database import SessionLocal
from app.models.history import NetworkHistory
from app.services.bandwidth_monitor import bandwidth_monitor
from app.services.protocol_analysis import protocol_analysis_service
from app.services.packet_capture import packet_capture_service

logger = logging.getLogger(__name__)


class HistoryService:
    def __init__(self, interval: int = 5, retention_limit: int = 10000):
        self.interval = interval
        self.retention_limit = retention_limit
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

    def start(self):
        with self.lock:
            if self.thread is None or not self.thread.is_alive():
                self.stop_event.clear()
                self.thread = threading.Thread(target=self._run, daemon=True)
                self.thread.start()
                logger.info(f"History service started with interval {self.interval} seconds")
            else:
                logger.warning("History service is already running")

    def stop(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                self.stop_event.set()
                self.thread.join(timeout=self.interval + 1)
                self.thread = None
                logger.info("History service stopped")
            else:
                logger.warning("History service is not running")

    def _run(self):
        while not self.stop_event.is_set():
            start_time = time.time()
            try:
                self._take_snapshot()
            except Exception as e:
                logger.error(f"Error taking history snapshot: {e}")
            # Sleep for the interval, but break early if stop_event is set
            elapsed = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed)
            # Wait for sleep_time seconds or until the event is set
            self.stop_event.wait(sleep_time)

    def _take_snapshot(self):
        # Get bandwidth stats for the selected interface (or None if none selected)
        # We want to get the stats for the selected interface, or if none, we can aggregate?
        # The bandwidth monitor has a method for selected interface and for all.
        # Since the snapshot is for the entire system, we might want to aggregate all interfaces?
        # However, the requirement says to store interface name if available.
        # Let's get the selected interface stats if one is selected, otherwise we can take the first interface or leave it blank?
        # For simplicity, we'll use the selected interface if set, otherwise we'll use None for interface and try to get total stats.

        # Get the selected interface name
        selected_interface = bandwidth_monitor.selected_interface

        # Get bandwidth stats for the selected interface (if any) or for all interfaces and sum?
        # The bandwidth monitor's get_selected_interface_stats returns stats for the selected interface.
        # If no interface is selected, we can get the stats for all interfaces and sum the rates?
        # But note: the bandwidth monitor's get_current_stats without argument returns a dict of all interfaces.
        # We'll do:
        if selected_interface:
            bw_stats = bandwidth_monitor.get_current_stats(selected_interface)
        else:
            # Get all interfaces and sum the rates?
            # However, note that the rates are per interface. Summing rates across interfaces doesn't make much sense
            # because they are on different interfaces. But for a system-wide view, we might want to aggregate.
            # Alternatively, we can leave the interface field blank and set the rates to 0?
            # Let's change the approach: we'll store the snapshot for the selected interface only, and if none is selected, we don't store.
            # But the requirement says to store the interface name if available. So if none is selected, we can set interface to None and still store the aggregated totals?
            # Let's look at the bandwidth monitor: it has a method to get stats for all interfaces (get_current_stats without argument).
            # We'll get all interfaces and sum the bytes and packets, but note that the rates (bps) are per second and we can sum them?
            # Actually, the rates are already per second, so summing them across interfaces would give the total bits per second across all interfaces.
            # This is acceptable for a system-wide view.
            all_stats = bandwidth_monitor.get_current_stats()
            if not all_stats:
                # No interfaces, return
                return
            # We'll sum the values
            total_download_bps = 0.0
            total_upload_bps = 0.0
            total_bytes_sent = 0
            total_bytes_recv = 0
            total_packets_sent = 0
            total_packets_recv = 0
            for stats in all_stats.values():
                total_download_bps += stats.get('download_bps', 0)
                total_upload_bps += stats.get('upload_bps', 0)
                total_bytes_sent += stats.get('total_bytes_sent', 0)
                total_bytes_recv += stats.get('total_bytes_recv', 0)
                total_packets_sent += stats.get('total_packets_sent', 0)
                total_packets_recv += stats.get('total_packets_recv', 0)
            bw_stats = {
                'interface': None,  # We don't have a single interface
                'download_bps': total_download_bps,
                'upload_bps': total_upload_bps,
                'total_bytes_sent': total_bytes_sent,
                'total_bytes_recv': total_bytes_recv,
                'total_packets_sent': total_packets_sent,
                'total_packets_recv': total_packets_recv
            }

        # Get protocol stats
        protocol_stats = protocol_analysis_service.get_protocol_stats()
        overall = protocol_stats.get('overall', {})
        protocols = protocol_stats.get('protocols', {})

        # Extract the counts we need
        total_packets = overall.get('total_packets', 0)
        total_bytes = overall.get('total_bytes', 0)
        tcp_packets = protocols.get('tcp', {}).get('packet_count', 0)
        udp_packets = protocols.get('udp', {}).get('packet_count', 0)
        icmp_packets = protocols.get('icmp', {}).get('packet_count', 0)
        arp_packets = protocols.get('arp', {}).get('packet_count', 0)

        # Create the history record
        db = SessionLocal()
        try:
            history_record = NetworkHistory(
                timestamp=datetime.now(timezone.utc),
                interface=bw_stats.get('interface'),
                download_rate=int(bw_stats.get('download_bps', 0)),  # Convert to int for storage
                upload_rate=int(bw_stats.get('upload_bps', 0)),
                total_packets=total_packets,
                total_bytes=total_bytes,
                tcp_packets=tcp_packets,
                udp_packets=udp_packets,
                icmp_packets=icmp_packets,
                arp_packets=arp_packets
            )
            db.add(history_record)
            db.commit()
            logger.debug(f"Stored history snapshot: {history_record.timestamp}")
            # Enforce retention policy
            self._enforce_retention(db)
        except Exception as e:
            logger.error(f"Failed to store history snapshot: {e}")
            db.rollback()
        finally:
            db.close()

    def _enforce_retention(self, db: SessionLocal):
        """Enforce the retention limit by deleting the oldest snapshots if we exceed the limit."""
        try:
            # Count total records
            total_count = db.query(NetworkHistory).count()
            if total_count > self.retention_limit:
                # Number of records to delete
                to_delete = total_count - self.retention_limit
                # Get the ids of the oldest 'to_delete' records
                subquery = db.query(NetworkHistory.id).order_by(NetworkHistory.timestamp.asc()).limit(to_delete).subquery()
                # Delete the records with those ids
                stmt = delete(NetworkHistory).where(NetworkHistory.id.in_(subquery))
                db.execute(stmt)
                db.commit()
                logger.info(f"Enforced retention policy: deleted {to_delete} old snapshots")
        except Exception as e:
            logger.error(f"Failed to enforce retention policy: {e}")
            db.rollback()