from uuid import uuid7

from sqlalchemy.ext.asyncio import AsyncSession

from solar_sites.modules.sites import repository
from solar_sites.modules.sites.models import Site
from solar_sites.modules.sites.schemas import SiteInput
from solar_sites.shared.errors import AppError


async def list_sites(db: AsyncSession, *, user_id: str) -> list[Site]:
    async with db.begin():
        return await repository.list_sites(db, user_id=user_id)


async def get_site(db: AsyncSession, *, user_id: str, site_id: str) -> Site:
    async with db.begin():
        return await _get_site(db, user_id=user_id, site_id=site_id)


async def _get_site(db: AsyncSession, *, user_id: str, site_id: str) -> Site:
    site = await repository.get_site(db, user_id=user_id, site_id=site_id)
    if site is None:
        raise AppError("NOT_FOUND", "Site not found.")
    return site


async def create_site(db: AsyncSession, *, user_id: str, data: SiteInput) -> Site:
    site = Site(id=str(uuid7()), user_id=user_id, **data.model_dump())
    async with db.begin():
        await repository.add_site(db, site=site)
    return site


async def update_site(db: AsyncSession, *, user_id: str, site_id: str, data: SiteInput) -> Site:
    async with db.begin():
        site = await _get_site(db, user_id=user_id, site_id=site_id)
        await repository.update_site(
            db,
            site=site,
            client_name=data.client_name,
            address=data.address,
            latitude=data.latitude,
            longitude=data.longitude,
            roof_area_m2=data.roof_area_m2,
            peak_kwp=data.peak_kwp,
        )
    return site


async def delete_site(db: AsyncSession, *, user_id: str, site_id: str) -> None:
    async with db.begin():
        site = await _get_site(db, user_id=user_id, site_id=site_id)
        await repository.delete_site(db, site=site)
