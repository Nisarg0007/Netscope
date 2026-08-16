import psutil

# Check what constants are available
print("Available attributes with 'AF':")
for attr in dir(psutil):
    if 'AF' in attr:
        print(f"  {attr}: {getattr(psutil, attr)}")

# Test interface detection
print("\nNetwork interfaces:")
addrs = psutil.net_if_addrs()
stats = psutil.net_if_stats()
io_counters = psutil.net_io_counters(pernic=True)

for name, addr_list in addrs.items():
    print(f"\nInterface: {name}")
    for addr in addr_list:
        print(f"  Family: {addr.family}, Address: {addr.address}")

    if name in stats:
        stat = stats[name]
        print(f"  Status: {'up' if stat.isup else 'down'}, Speed: {stat.speed}MBPS")

    if name in io_counters:
        io = io_counters[name]
        print(f"  Bytes: {io.bytes_sent} sent / {io.bytes_recv} recv")
        print(f"  Packets: {io.packets_sent} sent / {io.packets_recv} recv")
    break  # Just show first interface for brevity