import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime
from app.services.packet_capture import packet_capture_service


class ProtocolAnalysisService:
    def __init__(self):
        self.lock = threading.Lock()
        # Last time we calculated packets per second
        self.last_calculation_time: Optional[float] = None
        self.last_packet_count: int = 0

    def get_protocol_stats(self) -> Dict[str, Any]:
        """
        Get protocol statistics including:
        - Per protocol: packet count, byte count, packet percentage, byte percentage
        - Overall: total packets, total bytes, packets per second, avg packet size, min, max packet size
        """
        with self.lock:
            # Get raw stats from packet capture service
            raw_stats = packet_capture_service.capture_stats.copy()
            packets = packet_capture_service.packets.copy()

        # Calculate overall statistics
        total_packets = raw_stats.get('total_packets', 0)
        total_bytes = raw_stats.get('total_bytes', 0)

        # Calculate packets per second
        packets_per_second = 0.0
        current_time = time.time()
        if self.last_calculation_time is not None and self.last_packet_count is not None:
            time_diff = current_time - self.last_calculation_time
            if time_diff > 0:
                packet_diff = total_packets - self.last_packet_count
                packets_per_second = packet_diff / time_diff

        # Update for next calculation
        self.last_calculation_time = current_time
        self.last_packet_count = total_packets

        # Calculate average packet size
        avg_packet_size = 0.0
        if total_packets > 0:
            avg_packet_size = total_bytes / total_packets

        # Get min and max packet size from raw stats (if available)
        min_packet_size = raw_stats.get('min_packet_size', 0)
        max_packet_size = raw_stats.get('max_packet_size', 0)

        # If min_packet_size is still infinity (no packets), set to 0
        if min_packet_size == float('inf'):
            min_packet_size = 0

        # Prepare per protocol stats
        protocols = ['tcp', 'udp', 'icmp', 'arp', 'other']
        protocol_stats = {}

        for protocol in protocols:
            packet_count = raw_stats.get(f'{protocol}_packets', 0)
            byte_count = raw_stats.get(f'{protocol}_bytes', 0)

            packet_percentage = 0.0
            byte_percentage = 0.0

            if total_packets > 0:
                packet_percentage = (packet_count / total_packets) * 100

            if total_bytes > 0:
                byte_percentage = (byte_count / total_bytes) * 100

            protocol_stats[protocol] = {
                'packet_count': packet_count,
                'byte_count': byte_count,
                'packet_percentage': round(packet_percentage, 2),
                'byte_percentage': round(byte_percentage, 2)
            }

        # Prepare overall stats
        overall_stats = {
            'total_packets': total_packets,
            'total_bytes': total_bytes,
            'packets_per_second': round(packets_per_second, 2),
            'average_packet_size': round(avg_packet_size, 2),
            'min_packet_size': min_packet_size,
            'max_packet_size': max_packet_size
        }

        return {
            'protocols': protocol_stats,
            'overall': overall_stats,
            'timestamp': datetime.fromtimestamp(current_time).isoformat()
        }

    def get_protocol_stats_simple(self) -> Dict[str, Any]:
        """Get a simplified version of protocol stats for frequent polling"""
        stats = self.get_protocol_stats()
        return {
            'protocols': stats['protocols'],
            'overall': stats['overall']
        }


# Global instance
protocol_analysis_service = ProtocolAnalysisService()