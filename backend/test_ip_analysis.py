"""
Test script for IP analysis service
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.packet_capture import packet_capture_service
from app.services.ip_analysis import ip_analysis_service


def test_ip_analysis_initial_state():
    """Test that IP analysis returns correct initial state"""
    print("Testing initial state...")

    # Clear any existing packets
    packet_capture_service.clear_packets()

    # Get source IP stats
    source_stats = ip_analysis_service.get_top_source_ips()
    dest_stats = ip_analysis_service.get_top_destination_ips()

    # Check structure
    assert 'source_ips' in source_stats
    assert 'destination_ips' in dest_stats
    assert 'total_unique_ips' in source_stats
    assert 'total_unique_ips' in dest_stats
    assert 'total_packets' in source_stats
    assert 'total_bytes' in source_stats
    assert 'timestamp' in source_stats
    assert 'timestamp' in dest_stats

    # Should be empty initially
    assert len(source_stats['source_ips']) == 0
    assert len(dest_stats['destination_ips']) == 0
    assert source_stats['total_unique_ips'] == 0
    assert dest_stats['total_unique_ips'] == 0
    assert source_stats['total_packets'] == 0
    assert source_stats['total_bytes'] == 0
    assert dest_stats['total_packets'] == 0
    assert dest_stats['total_bytes'] == 0

    print("Initial state test passed")


def test_ip_aggregation():
    """Test that IP aggregation works correctly"""
    print("Testing IP aggregation...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add packets manually to test the logic
    test_packets = [
        # TCP packet from 192.168.1.1 to 192.168.1.2
        {
            'timestamp': '2026-08-17T10:00:00',
            'length': 60,
            'protocol': 'tcp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 12345,
            'dst_port': 80
        },
        # UDP packet from 192.168.1.2 to 192.168.1.1
        {
            'timestamp': '2026-08-17T10:00:01',
            'length': 42,
            'protocol': 'udp',
            'src_ip': '192.168.1.2',
            'dst_ip': '192.168.1.1',
            'src_port': 53,
            'dst_port': 12345
        },
        # Another TCP packet from 192.168.1.1 to 8.8.8.8
        {
            'timestamp': '2026-08-17T10:00:02',
            'length': 74,
            'protocol': 'tcp',
            'src_ip': '192.168.1.1',
            'dst_ip': '8.8.8.8',
            'src_port': 12346,
            'dst_port': 53
        },
        # ICMP packet from 8.8.8.8 to 192.168.1.1
        {
            'timestamp': '2026-08-17T10:00:03',
            'length': 98,
            'protocol': 'icmp',
            'src_ip': '8.8.8.8',
            'dst_ip': '192.168.1.1'
        },
        # Another packet from 192.168.1.1 to 192.168.1.2 (same as first)
        {
            'timestamp': '2026-08-17T10:00:04',
            'length': 60,
            'protocol': 'tcp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 12347,
            'dst_port': 80
        }
    ]

    # Add packets to capture service
    with packet_capture_service.lock:
        for packet in test_packets:
            packet_capture_service.packets.append(packet)

            # Update stats like _packet_callback does
            packet_length = packet['length']
            protocol = packet.get('protocol', 'other')

            packet_capture_service.capture_stats['total_packets'] += 1
            packet_capture_service.capture_stats['total_bytes'] += packet_length

            # Update min/max packet size
            current_min = packet_capture_service.capture_stats['min_packet_size']
            current_max = packet_capture_service.capture_stats['max_packet_size']
            if packet_length < current_min:
                packet_capture_service.capture_stats['min_packet_size'] = packet_length
            if packet_length > current_max:
                packet_capture_service.capture_stats['max_packet_size'] = packet_length

            # Update protocol-specific counters
            if protocol == 'tcp':
                packet_capture_service.capture_stats['tcp_packets'] += 1
                packet_capture_service.capture_stats['tcp_bytes'] += packet_length
            elif protocol == 'udp':
                packet_capture_service.capture_stats['udp_packets'] += 1
                packet_capture_service.capture_stats['udp_bytes'] += packet_length
            elif protocol == 'icmp':
                packet_capture_service.capture_stats['icmp_packets'] += 1
                packet_capture_service.capture_stats['icmp_bytes'] += packet_length
            elif protocol == 'arp':
                packet_capture_service.capture_stats['arp_packets'] += 1
                packet_capture_service.capture_stats['arp_bytes'] += packet_length
            else:
                packet_capture_service.capture_stats['other_packets'] += 1
                packet_capture_service.capture_stats['other_bytes'] += packet_length

        # Keep only last 1000 packets
        if len(packet_capture_service.packets) > 1000:
            packet_capture_service.packets = packet_capture_service.packets[-1000:]

    # Get source IP stats
    source_stats = ip_analysis_service.get_top_source_ips(limit=10, sort_by="packet_count")

    # Should have 3 unique source IPs: 192.168.1.1 (3 packets), 192.168.1.2 (1 packet), 8.8.8.8 (1 packet)
    assert source_stats['total_unique_ips'] == 3
    assert source_stats['total_packets'] == 5  # Total packets we added

    # Find 192.168.1.1 stats (should be top with 3 packets)
    ip_192_168_1_1 = None
    for ip_stat in source_stats['source_ips']:
        if ip_stat['ip_address'] == '192.168.1.1':
            ip_192_168_1_1 = ip_stat
            break

    assert ip_192_168_1_1 is not None
    assert ip_192_168_1_1['packet_count'] == 3
    assert ip_192_168_1_1['total_bytes'] == 60 + 74 + 60  # 194 bytes

    # Check percentages
    expected_packet_percentage = round((3/5) * 100, 2)  # 60.0
    expected_byte_percentage = round((194/334) * 100, 2)  # ~58.08

    assert ip_192_168_1_1['packet_percentage'] == expected_packet_percentage
    assert abs(ip_192_168_1_1['byte_percentage'] - expected_byte_percentage) < 0.01

    # Get destination IP stats
    dest_stats = ip_analysis_service.get_top_destination_ips(limit=10, sort_by="packet_count")

    # Should have 3 unique destination IPs: 192.168.1.2 (2 packets), 8.8.8.8 (1 packet), 192.168.1.1 (2 packets)
    assert dest_stats['total_unique_ips'] == 3
    assert dest_stats['total_packets'] == 5  # Total packets we added

    # Find 192.168.1.2 stats (should be top with 2 packets)
    ip_192_168_1_2_dest = None
    for ip_stat in dest_stats['destination_ips']:
        if ip_stat['ip_address'] == '192.168.1.2':
            ip_192_168_1_2_dest = ip_stat
            break

    assert ip_192_168_1_2_dest is not None
    assert ip_192_168_1_2_dest['packet_count'] == 2
    assert ip_192_168_1_2_dest['total_bytes'] == 60 + 60  # 120 bytes (two packets from 192.168.1.1)

    # Check sorting by bytes
    source_stats_bytes = ip_analysis_service.get_top_source_ips(limit=10, sort_by="bytes")
    # First item should have highest byte count
    if len(source_stats_bytes['source_ips']) > 0:
        first_ip = source_stats_bytes['source_ips'][0]
        # 192.168.1.1 has 194 bytes, which should be highest
        assert first_ip['ip_address'] == '192.168.1.1'
        assert first_ip['total_bytes'] == 194

    print("IP aggregation test passed")


def test_limit_parameter():
    """Test that limit parameter works correctly"""
    print("Testing limit parameter...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add packets from many different IPs
    test_packets = []
    for i in range(20):
        test_packets.append({
            'timestamp': '2026-08-17T10:00:00',
            'length': 60,
            'protocol': 'tcp',
            'src_ip': f'10.0.0.{i}',
            'dst_ip': '192.168.1.1',
            'src_port': 12345 + i,
            'dst_port': 80
        })

    # Add packets to capture service
    with packet_capture_service.lock:
        for packet in test_packets:
            packet_capture_service.packets.append(packet)
            # Update basic stats
            packet_capture_service.capture_stats['total_packets'] += 1
            packet_capture_service.capture_stats['total_bytes'] += packet['length']

    # Test with limit=5
    limited_stats = ip_analysis_service.get_top_source_ips(limit=5, sort_by="packet_count")
    assert len(limited_stats['source_ips']) == 5
    assert limited_stats['total_unique_ips'] == 20  # Actually 20 unique IPs

    # Test with limit=50 (more than available)
    unlimited_stats = ip_analysis_service.get_top_source_ips(limit=50, sort_by="packet_count")
    assert len(unlimited_stats['source_ips']) == 20  # Should return all 20

    print("Limit parameter test passed")


def test_sorting():
    """Test that sorting works correctly"""
    print("Testing sorting...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add packets with different byte counts
    test_packets = [
        {
            'timestamp': '2026-08-17T10:00:00',
            'length': 100,
            'protocol': 'tcp',
            'src_ip': '10.0.0.1',
            'dst_ip': '192.168.1.1'
        },
        {
            'timestamp': '2026-08-17T10:00:01',
            'length': 50,
            'protocol': 'tcp',
            'src_ip': '10.0.0.2',
            'dst_ip': '192.168.1.1'
        },
        {
            'timestamp': '2026-08-17T10:00:02',
            'length': 200,
            'protocol': 'tcp',
            'src_ip': '10.0.0.3',
            'dst_ip': '192.168.1.1'
        }
    ]

    # Add packets to capture service
    with packet_capture_service.lock:
        for packet in test_packets:
            packet_capture_service.packets.append(packet)
            packet_capture_service.capture_stats['total_packets'] += 1
            packet_capture_service.capture_stats['total_bytes'] += packet['length']

    # Test sorting by bytes (descending)
    stats_bytes = ip_analysis_service.get_top_source_ips(limit=10, sort_by="bytes")
    assert len(stats_bytes['source_ips']) == 3
    # Should be ordered: 10.0.0.3 (200), 10.0.0.1 (100), 10.0.0.2 (50)
    assert stats_bytes['source_ips'][0]['ip_address'] == '10.0.0.3'
    assert stats_bytes['source_ips'][0]['total_bytes'] == 200
    assert stats_bytes['source_ips'][1]['ip_address'] == '10.0.0.1'
    assert stats_bytes['source_ips'][1]['total_bytes'] == 100
    assert stats_bytes['source_ips'][2]['ip_address'] == '10.0.0.2'
    assert stats_bytes['source_ips'][2]['total_bytes'] == 50

    # Test sorting by packet count (all have 1 packet, so order may vary but should be stable)
    stats_count = ip_analysis_service.get_top_source_ips(limit=10, sort_by="packet_count")
    assert len(stats_count['source_ips']) == 3
    # All should have packet_count = 1
    for ip_stat in stats_count['source_ips']:
        assert ip_stat['packet_count'] == 1

    print("Sorting test passed")


def test_clear_packets():
    """Test that clearing packets resets IP stats"""
    print("Testing clear packets...")

    # Add a packet first
    with packet_capture_service.lock:
        packet_capture_service.packets.append({
            'timestamp': '2026-08-17T10:00:00',
            'length': 60,
            'protocol': 'tcp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2'
        })
        packet_capture_service.capture_stats['total_packets'] += 1
        packet_capture_service.capture_stats['total_bytes'] += 60

    # Verify we have data
    stats_before = ip_analysis_service.get_top_source_ips()
    assert len(stats_before['source_ips']) > 0
    assert stats_before['total_packets'] > 0

    # Clear packets
    packet_capture_service.clear_packets()

    # Verify data is cleared
    stats_after = ip_analysis_service.get_top_source_ips()
    assert len(stats_after['source_ips']) == 0
    assert stats_after['total_packets'] == 0
    assert stats_after['total_bytes'] == 0

    print("Clear packets test passed")


def test_ipv6_support():
    """Test that IPv6 addresses are handled correctly"""
    print("Testing IPv6 support...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add IPv6 packets
    test_packets = [
        {
            'timestamp': '2026-08-17T10:00:00',
            'length': 80,
            'protocol': 'tcp',
            'src_ip': '2001:db8::1',
            'dst_ip': '2001:db8::2'
        },
        {
            'timestamp': '2026-08-17T10:00:01',
            'length': 90,
            'protocol': 'udp',
            'src_ip': '2001:db8::2',
            'dst_ip': '2001:db8::1'
        }
    ]

    # Add packets to capture service
    with packet_capture_service.lock:
        for packet in test_packets:
            packet_capture_service.packets.append(packet)
            packet_capture_service.capture_stats['total_packets'] += 1
            packet_capture_service.capture_stats['total_bytes'] += packet['length']

    # Test that IPv6 addresses are processed
    source_stats = ip_analysis_service.get_top_source_ips()
    assert source_stats['total_unique_ips'] == 2
    assert source_stats['total_packets'] == 2

    # Check that both IPv6 addresses are present
    ip_addresses = [ip['ip_address'] for ip in source_stats['source_ips']]
    assert '2001:db8::1' in ip_addresses
    assert '2001:db8::2' in ip_addresses

    print("IPv6 support test passed")


if __name__ == "__main__":
    print("Running IP analysis tests...")
    try:
        test_ip_analysis_initial_state()
        test_ip_aggregation()
        test_limit_parameter()
        test_sorting()
        test_clear_packets()
        test_ipv6_support()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)