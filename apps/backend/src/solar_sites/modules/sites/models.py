from sqlalchemy import REAL, CheckConstraint, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from solar_sites.infra.database import Base


class Site(Base):
    __tablename__ = "sites"
    __table_args__ = (
        CheckConstraint("length(trim(client_name)) BETWEEN 1 AND 200"),
        CheckConstraint("length(trim(address)) BETWEEN 1 AND 500"),
        CheckConstraint("latitude BETWEEN -90 AND 90"),
        CheckConstraint("longitude BETWEEN -180 AND 180"),
        CheckConstraint("roof_area_m2 IS NULL OR roof_area_m2 > 0 AND roof_area_m2 <= 1000000"),
        CheckConstraint("peak_kwp > 0 AND peak_kwp <= 100000"),
        Index("ix_sites_user_id", "user_id"),
        {"sqlite_strict": True},
    )
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    client_name: Mapped[str] = mapped_column(Text)
    address: Mapped[str] = mapped_column(Text)
    latitude: Mapped[float] = mapped_column(REAL)
    longitude: Mapped[float] = mapped_column(REAL)
    roof_area_m2: Mapped[float | None] = mapped_column(REAL)
    peak_kwp: Mapped[float] = mapped_column(REAL)
