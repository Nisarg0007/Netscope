from sqlalchemy import Column, Integer, BigInteger, DateTime, String
from app.database import Base
from datetime import datetime, timezone


class NetworkHistory(Base):
    __tablename__ = "network_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    interface = Column(String, nullable=True)
    download_rate = Column(BigInteger, default=0)  # in bits per second
    upload_rate = Column(BigInteger, default=0)  # in bits per second
    total_packets = Column(Integer, default=0)
    total_bytes = Column(BigInteger, default=0)
    tcp_packets = Column(Integer, default=0)
    udp_packets = Column(Integer, default=0)
    icmp_packets = Column(Integer, default=0)
    arp_packets = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "interface": self.interface,
            "download_rate": self.download_rate,
            "upload_rate": self.upload_rate,
            "total_packets": self.total_packets,
            "total_bytes": self.total_bytes,
            "tcp_packets": self.tcp_packets,
            "udp_packets": self.udp_packets,
            "icmp_packets": self.icmp_packets,
            "arp_packets": self.arp_packets
        }