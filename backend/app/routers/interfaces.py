from fastapi import APIRouter
import psutil
from app.services.bandwidth_monitor import bandwidth_monitor

router = APIRouter()

@router.get("/interfaces")
async def get_network_interfaces():
    interfaces = []

    # Get address information
    addrs = psutil.net_if_addrs()
    # Get status information
    stats = psutil.net_if_stats()
    # Get IO counters
    io_counters = psutil.net_io_counters(pernic=True)

    for interface_name, addresses in addrs.items():
        ipv4 = None
        ipv6 = None
        mac = None

        for addr in addresses:
            # Use numeric values since psutil constants may not be available
            if addr.family == 2:  # AF_INET (IPv4)
                ipv4 = addr.address
            elif addr.family == 23:  # AF_INET6 (IPv6)
                ipv6 = addr.address
            elif addr.family == -1:  # AF_LINK (MAC)
                mac = addr.address

        # Get interface status
        is_up = stats.get(interface_name, None)
        status = "up" if is_up and is_up.isup else "down"

        # Get IO counters
        io = io_counters.get(interface_name, None)
        bytes_sent = io.bytes_sent if io else 0
        bytes_recv = io.bytes_recv if io else 0
        packets_sent = io.packets_sent if io else 0
        packets_recv = io.packets_recv if io else 0

        interfaces.append({
            "name": interface_name,
            "ipv4": ipv4,
            "ipv6": ipv6,
            "mac": mac,
            "status": status,
            "bytes_sent": bytes_sent,
            "bytes_received": bytes_recv,
            "packets_sent": packets_sent,
            "packets_received": packets_recv
        })

    return {"interfaces": interfaces}

@router.post("/interfaces/select/{interface_name}")
async def select_interface(interface_name: str):
    """Select an interface for bandwidth monitoring"""
    bandwidth_monitor.set_selected_interface(interface_name)
    bandwidth_monitor.start_monitoring()
    return {"message": f"Monitoring started for interface {interface_name}"}

@router.post("/interfaces/deselect")
async def deselect_interface():
    """Stop monitoring the selected interface"""
    bandwidth_monitor.set_selected_interface(None)
    bandwidth_monitor.stop_monitoring_thread()
    return {"message": "Interface monitoring stopped"}