# -- scripts imports --
from app.database import Base
# -- env imports --
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy import Column, String, text
from geoalchemy2 import Geometry


# === WEB GENERAL SCHEMA ===
class MissionDataRow(Base):
    __tablename__ = "missions_data"
    __table_args__ = {'schema': 'web_general'}

    uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    mission_name_english = Column(String)
    mission_name_hebrew = Column(String)
    ui_schema = Column(JSONB, default=[])


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
class GenericRuleRow(Base):
    __tablename__ = "rules"
    __table_args__ = {'schema': 'missions'}

    uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    mission_uuid = Column(UUID(as_uuid=True))
    name = Column(String)
    description = Column(String)
    value = Column(String)
    geometry_uuids = Column(ARRAY(UUID(as_uuid=True)))
    parameters = Column(JSONB, default={})