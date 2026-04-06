from sqlalchemy import Column, String, Integer, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from geoalchemy2 import Geometry
from app.database import Base

# === WEB GENERAL SCHEMA ===

class MissionDataRow(Base):
    __tablename__ = "missions_data"
    __table_args__ = {'schema': 'web_general'}
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    mission_name_english = Column(String)
    mission_name_hebrew = Column(String)

class GeometryRow(Base):
    __tablename__ = "geometries"
    __table_args__ = {'schema': 'web_general'}
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    geometry_name = Column(String, nullable=False)
    created_by = Column(String, default="user")
    geometry = Column(Geometry('GEOMETRY', srid=4326))

class GeometryToTeamRow(Base):
    __tablename__ = "geometry_to_team"
    __table_args__ = {'schema': 'web_general'}
    
    geometry_uuid = Column(UUID(as_uuid=True), primary_key=True)
    mission_uuid = Column(UUID(as_uuid=True), primary_key=True)
    team_uuid = Column(UUID(as_uuid=True), primary_key=True)

class TeamRow(Base):
    __tablename__ = "teams"
    __table_args__ = {'schema': 'web_general'}
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

# === MISSIONS SCHEMA ===

class QAMissionRow(Base):
    __tablename__ = "qa"
    __table_args__ = {'schema': 'missions'}
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    code_name = Column(String)
    frequency = Column(String)
    code_type = Column(String)
    geometry_uuids = Column(ARRAY(UUID(as_uuid=True)))
    checks_amount = Column(Integer, default=1)
    check_precent = Column(Integer, default=100)

class NewMissionRow(Base):
    __tablename__ = "new_missions"
    __table_args__ = {'schema': 'missions'}
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    nm_values = Column(String)
    status = Column(String)
    type = Column(String)
    geometry_uuids = Column(ARRAY(UUID(as_uuid=True)))
    h_values = Column(String, default="default")
    nm_id = Column(String, default="default")
    mpt_values = Column(String, default="default")
