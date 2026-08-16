"""
Test script for protocol analysis service
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.packet_capture import packet_capture_service
from app.services.protocol_analysis import protocol_analysis_service


def test_protocol_analysis_initial_state():
    """Test that protocol analysis returns correct initial state"""
    print("Testing initial state...")

    # Clear any existing packets
    packet_capture_service.clear_packets()

    # Get protocol stats
    stats = protocol_analysis_service.get_protocol_stats()

    # Check structure
    assert 'protocols' in stats
    assert 'overall' in stats
    assert 'timestamp' in stats

    # Check protocol structure
    expected_protocols = ['tcp', 'udp', 'icmp', 'arp', 'other']
    for protocol in expected_protocols:
        assert protocol in stats['protocols']
        proto_stats = stats['protocols'][protocol]
        assert 'packet_count' in proto_stats
        assert 'byte_count' in proto_stats
        assert 'packet_percentage' in proto_stats
        assert 'byte_percentage' in proto_stats

        # Initial state should have zeros
        assert proto_stats['packet_count'] == 0
        assert proto_stats['byte_count'] == 0
        assert proto_stats['packet_percentage'] == 0.0
        assert proto_stats['byte_percentage'] == 0.0

    # Check overall stats
    overall = stats['overall']
    assert overall['total_packets'] == 0
    assert overall['total_bytes'] == 0
    # packets_per_second can vary due to timing, just check it's a number
    assert isinstance(overall['packets_per_second'], (int, float))
    assert overall['average_packet_size'] == 0.0
    assert overall['min_packet_size'] == 0
    assert overall['max_packet_size'] == 0

    print("Initial state test passed")


def test_packet_processing():
    """Test that packet processing updates stats correctly"""
    print("Testing packet processing...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Simulate adding some packets manually to test the logic
    # This simulates what would happen in _packet_callback

    # Add a TCP packet (60 bytes)
    with packet_capture_service.lock:
        packet_capture_service.packets.append({
            'timestamp': '2026-08-17T10:00:00',
            'length': 60,
            'protocol': 'tcp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 12345,
            'dst_port': 80
        })

        # Manually update stats like _packet_callback does
        packet_capture_service.capture_stats['total_packets'] += 1
        packet_capture_service.capture_stats['total_bytes'] += 60
        packet_capture_service.capture_stats['min_packet_size'] = min(
            packet_capture_service.capture_stats['min_packet_size'], 60)
        packet_capture_service.capture_stats['max_packet_size'] = max(
            packet_capture_service.capture_stats['max_packet_size'], 60)
        packet_capture_service.capture_stats['tcp_packets'] += 1
        packet_capture_service.capture_stats['tcp_bytes'] += 60

    # Add a UDP packet (42 bytes)
    with packet_capture_service.lock:
        packet_capture_service.packets.append({
            'timestamp': '2026-08-17T10:00:01',
            'length': 42,
            'protocol': 'udp',
            'src_ip': '192.168.1.2',
            'dst_ip': '192.168.1.1',
            'src_port': 53,
            'dst_port': 12345
        })

        # Manually update stats like _packet_callback does
        packet_capture_service.capture_stats['total_packets'] += 1
        packet_capture_service.capture_stats['total_bytes'] += 42
        packet_capture_service.capture_stats['min_packet_size'] = min(
            packet_capture_service.capture_stats['min_packet_size'], 42)
        packet_capture_service.capture_stats['max_packet_size'] = max(
            packet_capture_service.capture_stats['max_packet_size'], 42)
        packet_capture_service.capture_stats['udp_packets'] += 1
        packet_capture_service.capture_stats['udp_bytes'] += 42

    # Add an ICMP packet (74 bytes)
    with packet_capture_service.lock:
        packet_capture_service.packets.append({
            'timestamp': '2026-08-17T10:00:02',
            'length': 74,
            'protocol': 'icmp',
            'src_ip': '192.168.1.1',
            'dst_ip': '8.8.8.8'
        })

        # Manually update stats like _packet_callback does
        packet_capture_service.capture_stats['total_packets'] += 1
        packet_capture_service.capture_stats['total_bytes'] += 74
        packet_capture_service.capture_stats['min_packet_size'] = min(
            packet_capture_service.capture_stats['min_packet_size'], 74)
        packet_capture_service.capture_stats['max_packet_size'] = max(
            packet_capture_service.capture_stats['max_packet_size'], 74)
        packet_capture_service.capture_stats['icmp_packets'] += 1
        packet_capture_service.capture_stats['icmp_bytes'] += 74

    # Get protocol stats
    stats = protocol_analysis_service.get_protocol_stats()

    # Check TCP stats
    tcp_stats = stats['protocols']['tcp']
    assert tcp_stats['packet_count'] == 1
    assert tcp_stats['byte_count'] == 60
    # Calculate expected percentages based on actual values
    total_packets = 3
    total_bytes = 176  # 60 + 42 + 74
    assert tcp_stats['packet_percentage'] == 33.33  # 1/3 * 100
    # Allow small floating point differences
    assert abs(tcp_stats['byte_percentage'] - (60/total_bytes*100)) < 0.01

    # Check UDP stats
    udp_stats = stats['protocols']['udp']
    assert udp_stats['packet_count'] == 1
    assert udp_stats['byte_count'] == 42
    assert udp_stats['packet_percentage'] == 33.33  # 1/3 * 100
    assert abs(udp_stats['byte_percentage'] - (42/total_bytes*100)) < 0.01

    # Check ICMP stats
    icmp_stats = stats['protocols']['icmp']
    assert icmp_stats['packet_count'] == 1
    assert icmp_stats['byte_count'] == 74
    assert icmp_stats['packet_percentage'] == 33.33  # 1/3 * 100
    assert abs(icmp_stats['byte_percentage'] - (74/total_bytes*100)) < 0.01

    # Check overall stats
    overall = stats['overall']
    assert overall['total_packets'] == 3
    assert overall['total_bytes'] == 176  # 60 + 42 + 74
    assert abs(overall['average_packet_size'] - (176/3)) < 0.01
    assert overall['min_packet_size'] == 42
    assert overall['max_packet_size'] == 74

    print("Packet processing test passed")


def test_clear_packets():
    """Test that clearing packets resets stats"""
    print("Testing clear packets...")

    # Clear packets
    packet_capture_service.clear_packets()

    # Get protocol stats
    stats = protocol_analysis_service.get_protocol_stats()

    # Check that everything is reset to zero
    for protocol in ['tcp', 'udp', 'icmp', 'arp', 'other']:
        proto_stats = stats['protocols'][protocol]
        assert proto_stats['packet_count'] == 0
        assert proto_stats['byte_count'] == 0
        assert proto_stats['packet_percentage'] == 0.0
        assert proto_stats['byte_percentage'] == 0.0

    overall = stats['overall']
    assert overall['total_packets'] == 0
    assert overall['total_bytes'] == 0
    # packets_per_second can vary due to timing, just check it's a number
    assert isinstance(overall['packets_per_second'], (int, float))
    assert overall['average_packet_size'] == 0.0
    assert overall['min_packet_size'] == 0
    assert overall['max_packet_size'] == 0

    print("Clear packets test passed")


if __name__ == "__main__":
    print("Running protocol analysis tests...")
    try:
        test_protocol_analysis_initial_state()
        test_packet_processing()
        test_clear_packets()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)