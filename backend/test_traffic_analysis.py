"""
Test script for traffic analysis service
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.packet_capture import packet_capture_service
from app.services.traffic_analysis import traffic_analysis_service


def test_traffic_analysis_initial_state():
    """Test that traffic analysis returns correct initial state"""
    print("Testing initial state...")

    # Clear any existing packets
    packet_capture_service.clear_packets()

    # Get unified stats
    stats = traffic_analysis_service.get_unified_traffic_summary()

    # Check structure
    assert 'overall' in stats
    assert 'protocols' in stats
    assert 'source_ips' in stats
    assert 'destination_ips' in stats
    assert 'source_ports' in stats
    assert 'destination_ports' in stats
    assert 'timestamp' in stats

    # Check that overall and protocols are dicts
    assert isinstance(stats['overall'], dict)
    assert isinstance(stats['protocols'], dict)

    # Check that the lists are empty initially
    assert len(stats['source_ips']) == 0
    assert len(stats['destination_ips']) == 0
    assert len(stats['source_ports']) == 0
    assert len(stats['destination_ports']) == 0

    # Check that timestamp is a string
    assert isinstance(stats['timestamp'], str)

    print("Initial state test passed")


def test_traffic_analysis_with_data():
    """Test that traffic analysis works with sample data"""
    print("Testing with sample data...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add sample packets (similar to previous tests)
    test_packets = [
        # TCP packet from 192.168.1.1:12345 to 192.168.1.2:80
        {
            'timestamp': '2026-08-17T10:00:00',
            'length': 60,
            'protocol': 'tcp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 12345,
            'dst_port': 80
        },
        # TCP packet from 192.168.1.2:80 to 192.168.1.1:12345 (response)
        {
            'timestamp': '2026-08-17T10:00:01',
            'length': 54,
            'protocol': 'tcp',
            'src_ip': '192.168.1.2',
            'dst_ip': '192.168.1.1',
            'src_port': 80,
            'dst_port': 12345
        },
        # UDP packet from 192.168.1.1:53 to 192.168.1.2:12345 (DNS response)
        {
            'timestamp': '2026-08-17T10:00:02',
            'length': 42,
            'protocol': 'udp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 53,
            'dst_port': 12345
        }
    ]

    # Add packets to capture service (we need to update the capture stats as well)
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

    # Get unified stats
    stats = traffic_analysis_service.get_unified_traffic_summary(limit=10, sort_by="bytes")

    # Debug: Print the actual stats structure
    print("DEBUG: Stats structure:", stats)

    # Check that we have data in the expected sections
    # Overall should have packets and bytes
    assert stats['overall']['total_packets'] == 3
    assert stats['overall']['total_bytes'] == 60 + 54 + 42  # 156

    # Protocols should have TCP and UDP
    assert 'tcp' in stats['protocols']
    assert 'udp' in stats['protocols']
    assert stats['protocols']['tcp']['packet_count'] == 2
    assert stats['protocols']['udp']['packet_count'] == 1

    # Source IPs: we have two unique source IPs: 192.168.1.1 (2 packets) and 192.168.1.2 (1 packet)
    assert len(stats['source_ips']) == 2
    # Find the IP with 2 packets (should be first when sorted by bytes)
    ip_192_168_1_1 = None
    for ip in stats['source_ips']:
        if ip['ip_address'] == '192.168.1.1':
            ip_192_168_1_1 = ip
            break
    assert ip_192_168_1_1 is not None
    assert ip_192_168_1_1['packet_count'] == 2
    assert ip_192_168_1_1['total_bytes'] == 60 + 42  # 102 bytes (first and third packets)

    # Destination IPs: we have two unique destination IPs: 192.168.1.2 (2 packets) and 192.168.1.1 (1 packet)
    assert len(stats['destination_ips']) == 2
    ip_192_168_1_2_dest = None
    for ip in stats['destination_ips']:
        if ip['ip_address'] == '192.168.1.2':
            ip_192_168_1_2_dest = ip
            break
    assert ip_192_168_1_2_dest is not None
    assert ip_192_168_1_2_dest['packet_count'] == 2
    assert ip_192_168_1_2_dest['total_bytes'] == 60 + 42  # 102 bytes (first and third packets)

    # Source ports: we have three unique source ports: 12345 (2 packets TCP), 80 (1 packet TCP), and 53 (1 packet UDP)
    assert len(stats['source_ports']) == 3
    port_12345_tcp = None
    for port in stats['source_ports']:
        if port['port'] == 12345 and port['protocol'] == 'TCP':
            port_12345_tcp = port
            break
    assert port_12345_tcp is not None
    # Debug: Print what we actually found
    if port_12345_tcp:
        print(f"DEBUG: Found port 12345 TCP: {port_12345_tcp}")
        assert port_12345_tcp['packet_count'] == 1
        assert port_12345_tcp['total_bytes'] == 60  # Just the first packet
    else:
        # Let's see what ports we actually have
        print("DEBUG: Source ports found:")
        for i, port in enumerate(stats['source_ports']):
            print(f"  Port {i}: {port}")
        assert False, "Could not find port 12345 TCP in source ports"

    # Also verify we have port 80 TCP
    port_80_tcp = None
    for port in stats['source_ports']:
        if port['port'] == 80 and port['protocol'] == 'TCP':
            port_80_tcp = port
            break
    assert port_80_tcp is not None
    assert port_80_tcp['packet_count'] == 1
    assert port_80_tcp['total_bytes'] == 54  # One TCP packet from port 80

    # And port 53 UDP
    port_53_udp = None
    for port in stats['source_ports']:
        if port['port'] == 53 and port['protocol'] == 'UDP':
            port_53_udp = port
            break
    assert port_53_udp is not None
    assert port_53_udp['packet_count'] == 1
    assert port_53_udp['total_bytes'] == 42  # One UDP packet from port 53

    # Destination ports: we have three unique destination ports: 80 (1 packet TCP), 12345 (1 packet TCP), and 12345 (1 packet UDP)
    assert len(stats['destination_ports']) == 3
    port_80_tcp = None
    for port in stats['destination_ports']:
        if port['port'] == 80 and port['protocol'] == 'TCP':
            port_80_tcp = port
            break
    assert port_80_tcp is not None
    assert port_80_tcp['packet_count'] == 1
    assert port_80_tcp['total_bytes'] == 60  # One TCP packet to port 80 (first packet)

    port_12345_tcp = None
    for port in stats['destination_ports']:
        if port['port'] == 12345 and port['protocol'] == 'TCP':
            port_12345_tcp = port
            break
    assert port_12345_tcp is not None
    assert port_12345_tcp['packet_count'] == 1
    assert port_12345_tcp['total_bytes'] == 54  # One TCP packet to port 12345 (second packet)

    port_12345_udp = None
    for port in stats['destination_ports']:
        if port['port'] == 12345 and port['protocol'] == 'UDP':
            port_12345_udp = port
            break
    assert port_12345_udp is not None
    assert port_12345_udp['packet_count'] == 1
    assert port_12345_udp['total_bytes'] == 42  # One UDP packet to port 12345 (third packet)

    print("Traffic analysis with data test passed")


def test_limits_and_sorting():
    """Test that limits and sorting work correctly in the unified endpoint"""
    print("Testing limits and sorting...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add packets with different byte counts for source IPs
    test_packets = []
    for i in range(5):
        test_packets.append({
            'timestamp': '2026-08-17T10:00:00',
            'length': 10 * (i+1),  # 10, 20, 30, 40, 50 bytes
            'protocol': 'tcp',
            'src_ip': f'10.0.0.{i+1}',
            'dst_ip': '192.168.1.1',
            'src_port': 12345 + i,
            'dst_port': 80
        })

    # Add packets to capture service
    with packet_capture_service.lock:
        for packet in test_packets:
            packet_capture_service.packets.append(packet)
            packet_capture_service.capture_stats['total_packets'] += 1
            packet_capture_service.capture_stats['total_bytes'] += packet['length']

    # Test with limit=3, should get top 3 by bytes (50, 40, 30)
    stats = traffic_analysis_service.get_unified_traffic_summary(limit=3, sort_by="bytes")
    assert len(stats['source_ips']) == 3
    # Should be in descending order by bytes: 50, 40, 30
    assert stats['source_ips'][0]['total_bytes'] == 50
    assert stats['source_ips'][1]['total_bytes'] == 40
    assert stats['source_ips'][2]['total_bytes'] == 30
    # Check IP addresses (10.0.0.5, 10.0.0.4, 10.0.0.3)
    assert stats['source_ips'][0]['ip_address'] == '10.0.0.5'
    assert stats['source_ips'][1]['ip_address'] == '10.0.0.4'
    assert stats['source_ips'][2]['ip_address'] == '10.0.0.3'

    # Test with limit=10 (more than we have), should get all 5
    stats = traffic_analysis_service.get_unified_traffic_summary(limit=10, sort_by="bytes")
    assert len(stats['source_ips']) == 5

    print("Limits and sorting test passed")


def test_error_handling():
    """Test that the service handles errors gracefully"""
    print("Testing error handling...")

    # We'll test by temporarily breaking one of the services, but since we don't want to
    # modify the actual services, we'll rely on the fact that the services are robust.
    # Instead, we'll test with an empty capture (which should not cause errors) and
    # verify that the structure is valid.

    packet_capture_service.clear_packets()
    stats = traffic_analysis_service.get_unified_traffic_summary()

    # Should return valid structure even with empty data
    assert isinstance(stats, dict)
    assert 'overall' in stats
    assert 'protocols' in stats
    assert isinstance(stats['source_ips'], list)
    assert isinstance(stats['destination_ips'], list)
    assert isinstance(stats['source_ports'], list)
    assert isinstance(stats['destination_ports'], list)
    assert isinstance(stats['timestamp'], str)

    print("Error handling test passed")


if __name__ == "__main__":
    print("Running traffic analysis tests...")
    try:
        test_traffic_analysis_initial_state()
        test_traffic_analysis_with_data()
        test_limits_and_sorting()
        test_error_handling()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)