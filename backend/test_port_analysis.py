"""
Test script for port analysis service
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.packet_capture import packet_capture_service
from app.services.port_analysis import port_analysis_service


def test_port_analysis_initial_state():
    """Test that port analysis returns correct initial state"""
    print("Testing initial state...")

    # Clear any existing packets
    packet_capture_service.clear_packets()

    # Get source port stats
    source_stats = port_analysis_service.get_top_source_ports()
    dest_stats = port_analysis_service.get_top_destination_ports()

    # Check structure
    assert 'source_ports' in source_stats
    assert 'destination_ports' in dest_stats
    assert 'total_unique_ports' in source_stats
    assert 'total_unique_ports' in dest_stats
    assert 'total_packets' in source_stats
    assert 'total_bytes' in source_stats
    assert 'timestamp' in source_stats
    assert 'timestamp' in dest_stats

    # Should be empty initially
    assert len(source_stats['source_ports']) == 0
    assert len(dest_stats['destination_ports']) == 0
    assert source_stats['total_unique_ports'] == 0
    assert dest_stats['total_unique_ports'] == 0
    assert source_stats['total_packets'] == 0
    assert source_stats['total_bytes'] == 0
    assert dest_stats['total_packets'] == 0
    assert dest_stats['total_bytes'] == 0

    print("Initial state test passed")


def test_port_aggregation_tcp():
    """Test that TCP port aggregation works correctly"""
    print("Testing TCP port aggregation...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add TCP packets manually to test the logic
    test_packets = [
        # TCP packet from source port 12345 to destination port 80 (HTTP)
        {
            'timestamp': '2026-08-17T10:00:00',
            'length': 60,
            'protocol': 'tcp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 12345,
            'dst_port': 80
        },
        # TCP packet from source port 12346 to destination port 443 (HTTPS)
        {
            'timestamp': '2026-08-17T10:00:01',
            'length': 74,
            'protocol': 'tcp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 12346,
            'dst_port': 443
        },
        # Another TCP packet from source port 12345 to destination port 80 (same source port)
        {
            'timestamp': '2026-08-17T10:00:02',
            'length': 60,
            'protocol': 'tcp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 12345,
            'dst_port': 80
        },
        # TCP packet from source port 80 to destination port 12345 (server response)
        {
            'timestamp': '2026-08-17T10:00:03',
            'length': 54,
            'protocol': 'tcp',
            'src_ip': '192.168.1.2',
            'dst_ip': '192.168.1.1',
            'src_port': 80,
            'dst_port': 12345
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

    # Get source port stats
    source_stats = port_analysis_service.get_top_source_ports(limit=10, sort_by="packet_count")

    # Should have 3 unique source ports: 12345 (2 packets), 12346 (1 packet), 80 (1 packet)
    assert source_stats['total_unique_ports'] == 3
    assert source_stats['total_packets'] == 4  # Total TCP packets we added

    # Find source port 12345 stats (should be top with 2 packets)
    port_12345_tcp = None
    for port_stat in source_stats['source_ports']:
        if port_stat['port'] == 12345 and port_stat['protocol'] == 'TCP':
            port_12345_tcp = port_stat
            break

    assert port_12345_tcp is not None
    assert port_12345_tcp['packet_count'] == 2
    assert port_12345_tcp['total_bytes'] == 60 + 60  # 120 bytes
    assert port_12345_tcp['common_service'] == "Unknown"  # 12345 not in common ports

    # Check percentages
    expected_packet_percentage = round((2/4) * 100, 2)  # 50.0
    expected_byte_percentage = round((120/248) * 100, 2)  # ~48.39

    assert port_12345_tcp['packet_percentage'] == expected_packet_percentage
    assert abs(port_12345_tcp['byte_percentage'] - expected_byte_percentage) < 0.01

    # Find source port 80 stats (should have HTTP service)
    port_80_tcp = None
    for port_stat in source_stats['source_ports']:
        if port_stat['port'] == 80 and port_stat['protocol'] == 'TCP':
            port_80_tcp = port_stat
            break

    assert port_80_tcp is not None
    assert port_80_tcp['packet_count'] == 1
    assert port_80_tcp['total_bytes'] == 54
    assert port_80_tcp['common_service'] == "HTTP"

    # Get destination port stats
    dest_stats = port_analysis_service.get_top_destination_ports(limit=10, sort_by="packet_count")

    # Should have 3 unique destination ports: 80 (2 packets), 443 (1 packet), 12345 (1 packet)
    assert dest_stats['total_unique_ports'] == 3
    assert dest_stats['total_packets'] == 4  # Total TCP packets we added

    # Find destination port 80 stats (should be top with 2 packets)
    port_80_tcp_dest = None
    for port_stat in dest_stats['destination_ports']:
        if port_stat['port'] == 80 and port_stat['protocol'] == 'TCP':
            port_80_tcp_dest = port_stat
            break

    assert port_80_tcp_dest is not None
    assert port_80_tcp_dest['packet_count'] == 2
    assert port_80_tcp_dest['total_bytes'] == 60 + 60  # 120 bytes (two packets to port 80)
    assert port_80_tcp_dest['common_service'] == "HTTP"

    print("TCP port aggregation test passed")


def test_port_aggregation_udp():
    """Test that UDP port aggregation works correctly"""
    print("Testing UDP port aggregation...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add UDP packets manually to test the logic
    test_packets = [
        # UDP packet from source port 12345 to destination port 53 (DNS)
        {
            'timestamp': '2026-08-17T10:00:00',
            'length': 42,
            'protocol': 'udp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 12345,
            'dst_port': 53
        },
        # UDP packet from source port 53 to destination port 12345 (DNS response)
        {
            'timestamp': '2026-08-17T10:00:01',
            'length': 54,
            'protocol': 'udp',
            'src_ip': '192.168.1.2',
            'dst_ip': '192.168.1.1',
            'src_port': 53,
            'dst_port': 12345
        },
        # Another UDP packet from source port 12345 to destination port 53 (same source port)
        {
            'timestamp': '2026-08-17T10:00:02',
            'length': 42,
            'protocol': 'udp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 12345,
            'dst_port': 53
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

    # Get source port stats
    source_stats = port_analysis_service.get_top_source_ports(limit=10, sort_by="packet_count")

    # Should have 2 unique source ports: 12345 (2 packets), 53 (1 packet)
    assert source_stats['total_unique_ports'] == 2
    assert source_stats['total_packets'] == 3  # Total UDP packets we added

    # Find source port 12345 UDP stats
    port_12345_udp = None
    for port_stat in source_stats['source_ports']:
        if port_stat['port'] == 12345 and port_stat['protocol'] == 'UDP':
            port_12345_udp = port_stat
            break

    assert port_12345_udp is not None
    assert port_12345_udp['packet_count'] == 2
    assert port_12345_udp['total_bytes'] == 42 + 42  # 84 bytes
    assert port_12345_udp['common_service'] == "Unknown"  # 12345 not in common ports

    # Find source port 53 UDP stats (should have DNS service)
    port_53_udp = None
    for port_stat in source_stats['source_ports']:
        if port_stat['port'] == 53 and port_stat['protocol'] == 'UDP':
            port_53_udp = port_stat
            break

    assert port_53_udp is not None
    assert port_53_udp['packet_count'] == 1
    assert port_53_udp['total_bytes'] == 54
    assert port_53_udp['common_service'] == "DNS"

    print("UDP port aggregation test passed")


def test_tcp_udp_same_port():
    """Test that TCP and UDP same port are handled as separate entries"""
    print("Testing TCP/UDP same port separation...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add TCP and UDP packets on same port number
    test_packets = [
        # TCP packet on port 443
        {
            'timestamp': '2026-08-17T10:00:00',
            'length': 60,
            'protocol': 'tcp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 12345,
            'dst_port': 443
        },
        # UDP packet on port 443 (different protocol, same port number)
        {
            'timestamp': '2026-08-17T10:00:01',
            'length': 42,
            'protocol': 'udp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2',
            'src_port': 12345,
            'dst_port': 443
        }
    ]

    # Add packets to capture service
    with packet_capture_service.lock:
        for packet in test_packets:
            packet_capture_service.packets.append(packet)
            packet_capture_service.capture_stats['total_packets'] += 1
            packet_capture_service.capture_stats['total_bytes'] += packet['length']

            # Update protocol-specific counters
            protocol = packet.get('protocol', 'other')
            if protocol == 'tcp':
                packet_capture_service.capture_stats['tcp_packets'] += 1
                packet_capture_service.capture_stats['tcp_bytes'] += packet['length']
            elif protocol == 'udp':
                packet_capture_service.capture_stats['udp_packets'] += 1
                packet_capture_service.capture_stats['udp_bytes'] += packet['length']

    # Get destination port stats
    dest_stats = port_analysis_service.get_top_destination_ports(limit=10, sort_by="packet_count")

    # Should have 2 unique port/protocol combinations: (443, TCP) and (443, UDP)
    assert dest_stats['total_unique_ports'] == 2
    assert dest_stats['total_packets'] == 2

    # Find TCP port 443 stats
    port_443_tcp = None
    for port_stat in dest_stats['destination_ports']:
        if port_stat['port'] == 443 and port_stat['protocol'] == 'TCP':
            port_443_tcp = port_stat
            break

    assert port_443_tcp is not None
    assert port_443_tcp['packet_count'] == 1
    assert port_443_tcp['total_bytes'] == 60
    assert port_443_tcp['common_service'] == "HTTPS"

    # Find UDP port 443 stats
    port_443_udp = None
    for port_stat in dest_stats['destination_ports']:
        if port_stat['port'] == 443 and port_stat['protocol'] == 'UDP':
            port_443_udp = port_stat
            break

    assert port_443_udp is not None
    assert port_443_udp['packet_count'] == 1
    assert port_443_udp['total_bytes'] == 42
    assert port_443_udp['common_service'] == "HTTPS"  # Same service mapping

    print("TCP/UDP same port separation test passed")


def test_limit_parameter():
    """Test that limit parameter works correctly"""
    print("Testing limit parameter...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add packets from many different source ports
    test_packets = []
    for i in range(20):
        test_packets.append({
            'timestamp': '2026-08-17T10:00:00',
            'length': 60,
            'protocol': 'tcp',
            'src_ip': '10.0.0.1',
            'dst_ip': '192.168.1.1',
            'src_port': 5000 + i,
            'dst_port': 80
        })

    # Add packets to capture service
    with packet_capture_service.lock:
        for packet in test_packets:
            packet_capture_service.packets.append(packet)
            packet_capture_service.capture_stats['total_packets'] += 1
            packet_capture_service.capture_stats['total_bytes'] += packet['length']

    # Test with limit=5
    limited_stats = port_analysis_service.get_top_source_ports(limit=5, sort_by="packet_count")
    assert len(limited_stats['source_ports']) == 5
    assert limited_stats['total_unique_ports'] == 20  # Actually 20 unique source ports

    # Test with limit=50 (more than available)
    unlimited_stats = port_analysis_service.get_top_source_ports(limit=50, sort_by="packet_count")
    assert len(unlimited_stats['source_ports']) == 20  # Should return all 20

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
            'dst_ip': '192.168.1.1',
            'src_port': 1001,
            'dst_port': 80
        },
        {
            'timestamp': '2026-08-17T10:00:01',
            'length': 50,
            'protocol': 'tcp',
            'src_ip': '10.0.0.2',
            'dst_ip': '192.168.1.1',
            'src_port': 1002,
            'dst_port': 80
        },
        {
            'timestamp': '2026-08-17T10:00:02',
            'length': 200,
            'protocol': 'tcp',
            'src_ip': '10.0.0.3',
            'dst_ip': '192.168.1.1',
            'src_port': 1003,
            'dst_port': 80
        }
    ]

    # Add packets to capture service
    with packet_capture_service.lock:
        for packet in test_packets:
            packet_capture_service.packets.append(packet)
            packet_capture_service.capture_stats['total_packets'] += 1
            packet_capture_service.capture_stats['total_bytes'] += packet['length']

    # Test sorting by bytes (descending)
    stats_bytes = port_analysis_service.get_top_source_ports(limit=10, sort_by="bytes")
    assert len(stats_bytes['source_ports']) == 3
    # Should be ordered: 1003 (200), 1001 (100), 1002 (50)
    assert stats_bytes['source_ports'][0]['port'] == 1003
    assert stats_bytes['source_ports'][0]['total_bytes'] == 200
    assert stats_bytes['source_ports'][1]['port'] == 1001
    assert stats_bytes['source_ports'][1]['total_bytes'] == 100
    assert stats_bytes['source_ports'][2]['port'] == 1002
    assert stats_bytes['source_ports'][2]['total_bytes'] == 50

    # Test sorting by packet count (all have 1 packet)
    stats_count = port_analysis_service.get_top_source_ports(limit=10, sort_by="packet_count")
    assert len(stats_count['source_ports']) == 3
    # All should have packet_count = 1
    for port_stat in stats_count['source_ports']:
        assert port_stat['packet_count'] == 1

    print("Sorting test passed")


def test_clear_packets():
    """Test that clearing packets resets port stats"""
    print("Testing clear packets...")

    # Add a packet first
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
        packet_capture_service.capture_stats['total_packets'] += 1
        packet_capture_service.capture_stats['total_bytes'] += 60

    # Verify we have data
    stats_before = port_analysis_service.get_top_source_ports()
    assert len(stats_before['source_ports']) > 0
    assert stats_before['total_packets'] > 0

    # Clear packets
    packet_capture_service.clear_packets()

    # Verify data is cleared
    stats_after = port_analysis_service.get_top_source_ports()
    assert len(stats_after['source_ports']) == 0
    assert stats_after['total_packets'] == 0
    assert stats_after['total_bytes'] == 0

    print("Clear packets test passed")


def test_ipv6_support():
    """Test that IPv6 TCP/UDP packets are handled correctly"""
    print("Testing IPv6 support...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add IPv6 TCP and UDP packets
    test_packets = [
        {
            'timestamp': '2026-08-17T10:00:00',
            'length': 80,
            'protocol': 'tcp',
            'src_ip': '2001:db8::1',
            'dst_ip': '2001:db8::2',
            'src_port': 12345,
            'dst_port': 80
        },
        {
            'timestamp': '2026-08-17T10:00:01',
            'length': 90,
            'protocol': 'udp',
            'src_ip': '2001:db8::2',
            'dst_ip': '2001:db8::1',
            'src_port': 53,
            'dst_port': 12345
        }
    ]

    # Add packets to capture service
    with packet_capture_service.lock:
        for packet in test_packets:
            packet_capture_service.packets.append(packet)
            packet_capture_service.capture_stats['total_packets'] += 1
            packet_capture_service.capture_stats['total_bytes'] += packet['length']

    # Test that IPv6 addresses are processed (ports should still be extracted)
    source_stats = port_analysis_service.get_top_source_ports()
    assert source_stats['total_unique_ports'] == 2
    assert source_stats['total_packets'] == 2

    # Check that both ports are present (regardless of IP version)
    source_ports = [port['port'] for port in source_stats['source_ports']]
    assert 12345 in source_ports
    assert 53 in source_ports

    print("IPv6 support test passed")


def test_non_tcp_udp_ignored():
    """Test that non-TCP/UDP packets are ignored"""
    print("Testing non-TCP/UDP packet ignoring...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add non-TCP/UDP packets (ICMP, ARP)
    test_packets = [
        {
            'timestamp': '2026-08-17T10:00:00',
            'length': 74,
            'protocol': 'icmp',
            'src_ip': '192.168.1.1',
            'dst_ip': '8.8.8.8'
        },
        {
            'timestamp': '2026-08-17T10:00:01',
            'length': 42,
            'protocol': 'arp',
            'src_ip': '192.168.1.1',
            'dst_ip': '192.168.1.2'
        }
    ]

    # Add packets to capture service
    with packet_capture_service.lock:
        for packet in test_packets:
            packet_capture_service.packets.append(packet)
            packet_capture_service.capture_stats['total_packets'] += 1
            packet_capture_service.capture_stats['total_bytes'] += packet['length']

    # Port stats should be empty since no TCP/UDP packets
    source_stats = port_analysis_service.get_top_source_ports()
    dest_stats = port_analysis_service.get_top_destination_ports()

    assert len(source_stats['source_ports']) == 0
    assert len(dest_stats['destination_ports']) == 0
    assert source_stats['total_packets'] == 0
    assert dest_stats['total_packets'] == 0

    print("Non-TCP/UDP packet ignoring test passed")


def test_common_service_mapping():
    """Test that common service mapping works correctly"""
    print("Testing common service mapping...")

    # Clear existing packets
    packet_capture_service.clear_packets()

    # Add packets for well-known ports
    test_packets = [
        {'timestamp': '2026-08-17T10:00:00', 'length': 60, 'protocol': 'tcp', 'src_port': 20, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:01', 'length': 60, 'protocol': 'tcp', 'src_port': 21, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:02', 'length': 60, 'protocol': 'tcp', 'src_port': 22, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:03', 'length': 60, 'protocol': 'tcp', 'src_port': 23, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:04', 'length': 60, 'protocol': 'tcp', 'src_port': 25, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:05', 'length': 60, 'protocol': 'tcp', 'src_port': 53, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:06', 'length': 60, 'protocol': 'tcp', 'src_port': 67, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:07', 'length': 60, 'protocol': 'tcp', 'src_port': 68, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:08', 'length': 60, 'protocol': 'tcp', 'src_port': 80, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:09', 'length': 60, 'protocol': 'tcp', 'src_port': 110, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:10', 'length': 60, 'protocol': 'tcp', 'src_port': 123, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:11', 'length': 60, 'protocol': 'tcp', 'src_port': 143, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:12', 'length': 60, 'protocol': 'tcp', 'src_port': 161, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:13', 'length': 60, 'protocol': 'tcp', 'src_port': 443, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:14', 'length': 60, 'protocol': 'tcp', 'src_port': 3306, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:15', 'length': 60, 'protocol': 'tcp', 'src_port': 5432, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:16', 'length': 60, 'protocol': 'tcp', 'src_port': 6379, 'dst_port': 80},
        {'timestamp': '2026-08-17T10:00:17', 'length': 60, 'protocol': 'tcp', 'src_port': 8080, 'dst_port': 80}
    ]

    # Add packets to capture service (only source ports matter for this test)
    with packet_capture_service.lock:
        for packet in test_packets:
            packet_capture_service.packets.append(packet)
            packet_capture_service.capture_stats['total_packets'] += 1
            packet_capture_service.capture_stats['total_bytes'] += packet['length']

    # Get source port stats
    source_stats = port_analysis_service.get_top_source_ports(limit=20, sort_by="packet_count")

    # Should have all 18 unique source ports
    assert source_stats['total_unique_ports'] == 18
    assert source_stats['total_packets'] == 18

    # Test specific service mappings
    expected_services = {
        20: "FTP", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        53: "DNS", 67: "DHCP", 68: "DHCP", 80: "HTTP", 110: "POP3",
        123: "NTP", 143: "IMAP", 161: "SNMP", 443: "HTTPS", 3306: "MySQL",
        5432: "PostgreSQL", 6379: "Redis", 8080: "HTTP Alternate"
    }

    for port_stat in source_stats['source_ports']:
        port_num = port_stat['port']
        expected_service = expected_services[port_num]
        actual_service = port_stat['common_service']
        assert actual_service == expected_service, f"Port {port_num}: expected {expected_service}, got {actual_service}"

    print("Common service mapping test passed")


if __name__ == "__main__":
    print("Running port analysis tests...")
    try:
        test_port_analysis_initial_state()
        test_port_aggregation_tcp()
        test_port_aggregation_udp()
        test_tcp_udp_same_port()
        test_limit_parameter()
        test_sorting()
        test_clear_packets()
        test_ipv6_support()
        test_non_tcp_udp_ignored()
        test_common_service_mapping()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)