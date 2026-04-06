from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class GeometryCreate(BaseModel):
    name: str
    type: str # 'Point' or 'Polygon'
    coordinates: Any
    
class RuleData(BaseModel):
    name: str
    description: str
    value: str
    missionId: str
    geometryIds: Optional[List[str]] = []
    geometryId: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class RuleCreate(BaseModel):
    rule: RuleData
    newGeo: Optional[GeometryCreate] = None
    newGeos: Optional[List[GeometryCreate]] = None
