from typing import Annotated

from fastapi import APIRouter, Path

from solar_sites.modules.auth import IdentityDep
from solar_sites.modules.sites import service
from solar_sites.modules.sites.schemas import SiteInput, SiteOutput
from solar_sites.platform.dependencies import SessionDep

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.get("", response_model=list[SiteOutput], operation_id="listSites")
async def list_sites(
    current_identity: IdentityDep,
    db: SessionDep,
) -> list[SiteOutput]:
    user_sites = await service.list_sites(db, user_id=current_identity.user_id)
    return [SiteOutput.model_validate(site) for site in user_sites]


@router.post("", status_code=201, response_model=SiteOutput, operation_id="createSite")
async def create_site(
    body: SiteInput,
    current_identity: IdentityDep,
    db: SessionDep,
) -> SiteOutput:
    site = await service.create_site(
        db,
        user_id=current_identity.user_id,
        data=body,
    )
    return SiteOutput.model_validate(site)


@router.get("/{id}", response_model=SiteOutput, operation_id="getSite")
async def get_site(
    site_id: Annotated[str, Path(alias="id")],
    current_identity: IdentityDep,
    db: SessionDep,
) -> SiteOutput:
    site = await service.get_site(
        db,
        user_id=current_identity.user_id,
        site_id=site_id,
    )
    return SiteOutput.model_validate(site)


@router.put("/{id}", response_model=SiteOutput, operation_id="updateSite")
async def update_site(
    site_id: Annotated[str, Path(alias="id")],
    body: SiteInput,
    current_identity: IdentityDep,
    db: SessionDep,
) -> SiteOutput:
    site = await service.update_site(
        db,
        user_id=current_identity.user_id,
        site_id=site_id,
        data=body,
    )
    return SiteOutput.model_validate(site)


@router.delete("/{id}", status_code=204, operation_id="deleteSite")
async def delete_site(
    site_id: Annotated[str, Path(alias="id")],
    current_identity: IdentityDep,
    db: SessionDep,
) -> None:
    await service.delete_site(
        db,
        user_id=current_identity.user_id,
        site_id=site_id,
    )
