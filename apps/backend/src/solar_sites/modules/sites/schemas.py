from typing import Annotated

from pydantic import ConfigDict, Field, StringConstraints

from solar_sites.platform.schemas import ApiModel

ClientName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Address = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class SiteInput(ApiModel):
    model_config = ConfigDict(validate_by_name=False)
    client_name: ClientName
    address: Address
    latitude: float = Field(ge=-90, le=90, strict=True)
    longitude: float = Field(ge=-180, le=180, strict=True)
    roof_area_m2: float | None = Field(default=None, gt=0, le=1_000_000, strict=True)
    peak_kwp: float = Field(gt=0, le=100_000, strict=True)


class SiteOutput(SiteInput):
    model_config = ConfigDict(from_attributes=True, validate_by_name=True)
    id: str
