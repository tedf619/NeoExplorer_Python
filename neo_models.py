import pydantic
from typing import List, Dict


class DiameterRange(pydantic.BaseModel):
    estimated_diameter_min: float
    estimated_diameter_max: float


class EstimatedDiameter(pydantic.BaseModel):
    kilometers: DiameterRange
    meters: DiameterRange


class RelativeVelocity(pydantic.BaseModel):
    kilometers_per_second: float
    kilometers_per_hour: float


class MissDistance(pydantic.BaseModel):
    astronomical: float
    lunar: float
    kilometers: float


class CloseApproachData(pydantic.BaseModel):
    close_approach_date: str
    close_approach_date_full: str
    relative_velocity: RelativeVelocity
    miss_distance: MissDistance
    orbiting_body: str


class NearEarthObject(pydantic.BaseModel):
    id: str
    name: str
    absolute_magnitude_h: float
    is_potentially_hazardous_asteroid: bool
    is_sentry_object: bool
    estimated_diameter: EstimatedDiameter
    close_approach_data: List[CloseApproachData]


class NeoFeedResponse(pydantic.BaseModel):
    element_count: int
    near_earth_objects: Dict[str, List[NearEarthObject]]
