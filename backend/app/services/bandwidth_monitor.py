import psutil
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from collections import defaultdict

class BandwidthMonitor:
    def __init__(self):
        # Store last measurement for each interface
        self.last_measurements: Dict[str, Dict[str, Any]] = {}
        # Store current calculated stats for each interface
        self.current_stats: Dict[str, Dict[str, Any]] = {}
        # Lock for thread safety
        self.lock = threading.Lock()
        # Monitoring thread
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_monitoring = False
        self.selected_interface: Optional[str] = None

    def start_monitoring(self):
        """Start the bandwidth monitoring in a background thread"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.stop_monitoring = False
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("Bandwidth monitoring started")

    def stop_monitoring_thread(self):
        """Stop the monitoring thread"""
        self.stop_monitoring = True
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        print("Bandwidth monitoring stopped")

    def set_selected_interface(self, interface_name: Optional[str]):
        """Set the interface to monitor for detailed stats"""
        self.selected_interface = interface_name
        print(f"Selected interface for monitoring: {interface_name}")

    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread"""
        while not self.stop_monitoring:
            try:
                self._update_bandwidth_stats()
                time.sleep(1)  # Update every second
            except Exception as e:
                print(f"Error in bandwidth monitoring: {e}")
                time.sleep(1)

    def _update_bandwidth_stats(self):
        """Update bandwidth statistics for all interfaces"""
        # Get current IO counters
        io_counters = psutil.net_io_counters(pernic=True)
        current_time = time.time()

        with self.lock:
            for interface_name, counters in io_counters.items():
                # Skip if we're only monitoring a specific interface and this isn't it
                if self.selected_interface and interface_name != self.selected_interface:
                    # Still update last_measurements for consistency, but don't calculate stats
                    if interface_name not in self.last_measurements:
                        self.last_measurements[interface_name] = {
                            'timestamp': current_time,
                            'bytes_sent': counters.bytes_sent,
                            'bytes_recv': counters.bytes_recv,
                            'packets_sent': counters.packets_sent,
                            'packets_recv': counters.packets_recv
                        }
                    continue

                # Initialize if first time seeing this interface
                if interface_name not in self.last_measurements:
                    self.last_measurements[interface_name] = {
                        'timestamp': current_time,
                        'bytes_sent': counters.bytes_sent,
                        'bytes_recv': counters.bytes_recv,
                        'packets_sent': counters.packets_sent,
                        'packets_recv': counters.packets_recv
                    }
                    # Set initial stats to zero
                    self.current_stats[interface_name] = {
                        'interface': interface_name,
                        'timestamp': datetime.fromtimestamp(current_time).isoformat(),
                        'download_bps': 0.0,
                        'upload_bps': 0.0,
                        'download_mbps': 0.0,
                        'upload_mbps': 0.0,
                        'total_bytes_sent': counters.bytes_sent,
                        'total_bytes_recv': counters.bytes_recv,
                        'total_packets_sent': counters.packets_sent,
                        'total_packets_recv': counters.packets_recv,
                        'packet_download_pps': 0.0,
                        'packet_upload_pps': 0.0
                    }
                    continue

                # Calculate delta
                last = self.last_measurements[interface_name]
                time_delta = current_time - last['timestamp']

                # Avoid division by zero
                if time_delta <= 0:
                    time_delta = 0.001

                # Calculate rates
                bytes_sent_delta = counters.bytes_sent - last['bytes_sent']
                bytes_recv_delta = counters.bytes_recv - last['bytes_recv']
                packets_sent_delta = counters.packets_sent - last['packets_sent']
                packets_recv_delta = counters.packets_recv - last['packets_recv']

                download_bps = bytes_recv_delta / time_delta
                upload_bps = bytes_sent_delta / time_delta
                download_mbps = download_bps / 1_000_000  # Convert to Mbps
                upload_mbps = upload_bps / 1_000_000
                packet_download_pps = packets_recv_delta / time_delta
                packet_upload_pps = packets_sent_delta / time_delta

                # Update current stats
                self.current_stats[interface_name] = {
                    'interface': interface_name,
                    'timestamp': datetime.fromtimestamp(current_time).isoformat(),
                    'download_bps': max(0, download_bps),  # Ensure non-negative
                    'upload_bps': max(0, upload_bps),
                    'download_mbps': max(0, download_mbps),
                    'upload_mbps': max(0, upload_mbps),
                    'total_bytes_sent': counters.bytes_sent,
                    'total_bytes_recv': counters.bytes_recv,
                    'total_packets_sent': counters.packets_sent,
                    'total_packets_recv': counters.packets_recv,
                    'packet_download_pps': max(0, packet_download_pps),
                    'packet_upload_pps': max(0, packet_upload_pps)
                }

                # Update last measurement
                self.last_measurements[interface_name] = {
                    'timestamp': current_time,
                    'bytes_sent': counters.bytes_sent,
                    'bytes_recv': counters.bytes_recv,
                    'packets_sent': counters.packets_sent,
                    'packets_recv': counters.packets_recv
                }

    def get_current_stats(self, interface_name: Optional[str] = None) -> Dict[str, Any]:
        """Get current bandwidth statistics"""
        with self.lock:
            if interface_name:
                return self.current_stats.get(interface_name, {})
            else:
                # Return stats for all interfaces
                return dict(self.current_stats)

    def get_selected_interface_stats(self) -> Dict[str, Any]:
        """Get stats for the currently selected interface"""
        if self.selected_interface:
            return self.get_current_stats(self.selected_interface)
        return {}

# Global instance
bandwidth_monitor = BandwidthMonitor()