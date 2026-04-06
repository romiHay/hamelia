from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field


class GeometryCreate(BaseModel):
    name: str
    type: str  # 'Point' or 'Polygon'
    coordinates: Union[List[float], List[List[float]]]


class RuleData(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    value: str
    missionId: str
    geometryIds: Optional[List[str]] = []
    geometryId: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RuleCreate(BaseModel):
    rule: RuleData
    newGeo: Optional[GeometryCreate] = None
    newGeos: Optional[List[GeometryCreate]] = None