from typing import Annotated, cast

from fastapi import Depends, Request

from solar_sites.modules.energy.solar_data_provider import SolarDataProvider


# solar provider
def get_solar_provider(request: Request) -> SolarDataProvider:
    return cast(SolarDataProvider, request.app.state.solar)


SolarDep = Annotated[SolarDataProvider, Depends(get_solar_provider)]
