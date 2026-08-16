import threading
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
try:
    from scapy.all import (
        sniff, IP, IPv6, TCP, UDP, ICMP, ARP,
        conf
    )
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    logging.warning("Scapy not available. Packet capture will be disabled.")

class PacketCaptureService:
    def __init__(self):
        self.capture_thread: Optional[threading.Thread] = None
        self.stop_capture = False
        self.selected_interface: Optional[str] = None
        self.packets: List[Dict[str, Any]] = []
        self.capture_stats = {
            'total_packets': 0,
            'tcp_packets': 0,
            'udp_packets': 0,
            'icmp_packets': 0,
            'arp_packets': 0,
            'ipv6_packets': 0,
            'other_packets': 0
        }
        self.is_capturing = False
        self.lock = threading.Lock()

        # Configure Scapy for Windows if needed
        if SCAPY_AVAILABLE:
            try:
                # Use WinPcap/Npcap on Windows
                conf.use_pcap = True
            except:
                pass  # Fall back to default

    def start_capture(self, interface: str) -> bool:
        """Start packet capture on the specified interface"""
        if not SCAPY_AVAILABLE:
            logging.error("Scapy not available. Cannot start packet capture.")
            return False

        if self.is_capturing:
            logging.warning("Capture already running.")
            return False

        try:
            self.selected_interface = interface
            self.stop_capture = False
            self.is_capturing = True

            # Clear previous packets and stats
            with self.lock:
                self.packets.clear()
                self.capture_stats = {
                    'total_packets': 0,
                    'tcp_packets': 0,
                    'udp_packets': 0,
                    'icmp_packets': 0,
                    'arp_packets': 0,
                    'ipv6_packets': 0,
                    'other_packets': 0
                }

            # Start capture thread
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                args=(interface,),
                daemon=True
            )
            self.capture_thread.start()
            logging.info(f"Packet capture started on interface {interface}")
            return True
        except Exception as e:
            logging.error(f"Failed to start packet capture: {e}")
            self.is_capturing = False
            return False

    def stop_capture(self) -> bool:
        """Stop packet capture"""
        if not self.is_capturing:
            return True

        self.stop_capture = True
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)
        self.is_capturing = False
        logging.info("Packet capture stopped")
        return True

    def get_capture_status(self) -> Dict[str, Any]:
        """Get current capture status"""
        with self.lock:
            return {
                'is_capturing': self.is_capturing,
                'selected_interface': self.selected_interface,
                'packet_count': len(self.packets),
                'stats': dict(self.capture_stats),
                'recent_packets': self.packets[-10:] if self.packets else []  # Last 10 packets
            }

    def get_packets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get captured packets"""
        with self.lock:
            return self.packets[-limit:] if self.packets else []

    def clear_packets(self):
        """Clear captured packets"""
        with self.lock:
            self.packets.clear()
            self.capture_stats = {
                'total_packets': 0,
                'tcp_packets': 0,
                'udp_packets': 0,
                'icmp_packets': 0,
                'arp_packets': 0,
                'ipv6_packets': 0,
                'other_packets': 0
            }

    def _capture_loop(self, interface: str):
        """Main capture loop"""
        try:
            # Sniff packets with a callback function
            sniff(
                iface=interface,
                prn=self._packet_callback,
                stop_filter=lambda x: self.stop_capture,
                store=False  # Don't store packets in scapy's internal buffer
            )
        except Exception as e:
            logging.error(f"Error in packet capture loop: {e}")
        finally:
            self.is_capturing = False

    def _packet_callback(self, packet):
        """Process each captured packet"""
        if self.stop_capture:
            return

        try:
            packet_info = self._extract_packet_info(packet)
            if packet_info:
                with self.lock:
                    self.packets.append(packet_info)
                    # Update stats
                    self.capture_stats['total_packets'] += 1
                    proto = packet_info.get('protocol', 'other')
                    if proto in self.capture_stats:
                        self.capture_stats[proto] += 1
                    else:
                        self.capture_stats['other_packets'] += 1

                # Keep only last 1000 packets to prevent memory issues
                with self.lock:
                    if len(self.packets) > 1000:
                        self.packets = self.packets[-1000:]
        except Exception as e:
            logging.debug(f"Error processing packet: {e}")

    def _extract_packet_info(self, packet) -> Optional[Dict[str, Any]]:
        """Extract metadata from a packet"""
        try:
            info = {
                'timestamp': datetime.fromtimestamp(packet.time).isoformat(),
                'length': len(packet),
                'protocol': 'unknown',
                'src_ip': None,
                'dst_ip': None,
                'src_port': None,
                'dst_port': None,
                'tcp_flags': None,
                'ttl': None
            }

            # Handle Ethernet layer (for ARP)
            if packet.haslayer('Ethernet'):
                # ARP handling
                if packet.haslayer(ARP):
                    arp = packet[ARP]
                    info.update({
                        'protocol': 'arp',
                        'src_ip': arp.psrc,
                        'dst_ip': arp.pdst,
                    })
                    return info

            # Handle IPv4
            if packet.haslayer(IP):
                ip = packet[IP]
                info.update({
                    'src_ip': ip.src,
                    'dst_ip': ip.dst,
                    'ttl': ip.ttl
                })

                # Handle TCP
                if packet.haslayer(TCP):
                    tcp = packet[TCP]
                    info.update({
                        'protocol': 'tcp',
                        'src_port': tcp.sport,
                        'dst_port': tcp.dport,
                        'tcp_flags': str(tcp.flags)
                    })
                    return info

                # Handle UDP
                elif packet.haslayer(UDP):
                    udp = packet[UDP]
                    info.update({
                        'protocol': 'udp',
                        'src_port': udp.sport,
                        'dst_port': udp.dport
                    })
                    return info

                # Handle ICMP
                elif packet.haslayer(ICMP):
                    info.update({
                        'protocol': 'icmp'
                    })
                    return info

                # Other IP protocols
                else:
                    info.update({
                        'protocol': 'ip'
                    })
                    return info

            # Handle IPv6
            if packet.haslayer(IPv6):
                ipv6 = packet[IPv6]
                info.update({
                    'src_ip': ipv6.src,
                    'dst_ip': ipv6.dst
                })

                # Handle TCP over IPv6
                if packet.haslayer(TCP):
                    tcp = packet[TCP]
                    info.update({
                        'protocol': 'tcp',
                        'src_port': tcp.sport,
                        'dst_port': tcp.dport,
                        'tcp_flags': str(tcp.flags)
                    })
                    return info

                # Handle UDP over IPv6
                elif packet.haslayer(UDP):
                    udp = packet[UDP]
                    info.update({
                        'protocol': 'udp',
                        'src_port': udp.sport,
                        'dst_port': udp.dport
                    })
                    return info

                # Handle ICMPv6
                elif packet.haslayer(ICMP):
                    info.update({
                        'protocol': 'icmpv6'
                    })
                    return info

                # Other IPv6
                else:
                    info.update({
                        'protocol': 'ipv6'
                    })
                    return info

        except Exception as e:
            logging.debug(f"Error extracting packet info: {e}")

        return None

# Global instance
packet_capture_service = PacketCaptureService()