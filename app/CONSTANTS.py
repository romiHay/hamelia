from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy import Column, String, Integer, text
from shapely.geometry import Point, Polygon, mapping
from typing import List, Optional, Any, Dict
from pydantic_settings import BaseSettings
from geoalchemy2 import shape, Geometry
from sqlalchemy.orm import Session
from geoalchemy2 import Geometry
from pydantic import BaseModel
from datetime import datetime
import traceback