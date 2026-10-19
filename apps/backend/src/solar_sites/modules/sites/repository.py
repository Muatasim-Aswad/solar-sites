from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from solar_sites.modules.sites.models import Site


async def list_sites(db: AsyncSession, *, user_id: str) -> list[Site]:
    sites = await db.scalars(select(Site).where(Site.user_id == user_id).order_by(Site.id))
    return list(sites)


async def get_site(db: AsyncSession, *, user_id: str, site_id: str) -> Site | None:
    return await db.scalar(select(Site).where(Site.id == site_id, Site.user_id == user_id))


async def add_site(db: AsyncSession, *, site: Site) -> None:
    db.add(site)
    await db.flush()


async def update_site(
    db: AsyncSession,
    *,
    site: Site,
    client_name: str,
    address: str,
    latitude: float,
    longitude: float,
    roof_area_m2: float | None,
    peak_kwp: float,
) -> None:
    site.client_name = client_name
    site.address = address
    site.latitude = latitude
    site.longitude = longitude
    site.roof_area_m2 = roof_area_m2
    site.peak_kwp = peak_kwp
    await db.flush()


async def delete_site(db: AsyncSession, *, site: Site) -> None:
    await db.delete(site)
    await db.flush()
