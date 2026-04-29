# -- scripts imports --
from app.database import Base
# -- env imports --
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy import Column, String, text, Index, DateTime, func
from geoalchemy2 import Geometry


# --- WEB GENERAL SCHEMA ---
class UserRow(Base):
   __tablename__ = "users"
   __table_args__ = {'schema': 'web_general'}
   uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
   username = Column(String, unique=True, nullable=False)
   full_name = Column(String)
   created_at = Column(DateTime(timezone=True), server_default=func.now())
   updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TeamRow(Base):
   __tablename__ = "teams"
   __table_args__ = {'schema': 'web_general'}
   uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
   name = Column(String, nullable=False)
   created_at = Column(DateTime(timezone=True), server_default=func.now())
   updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserToTeamRow(Base):
   __tablename__ = "user_to_team"
   __table_args__ = {'schema': 'web_general'}
   user_uuid = Column(UUID(as_uuid=True), primary_key=True)
   team_uuid = Column(UUID(as_uuid=True), primary_key=True)
   created_at = Column(DateTime(timezone=True), server_default=func.now())


class MissionDataRow(Base):
   __tablename__ = "missions_data"
   __table_args__ = {'schema': 'web_general'}

   uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
   mission_name_english = Column(String)
   mission_name_hebrew = Column(String)
   ui_schema = Column(JSONB, default=[])
   created_at = Column(DateTime(timezone=True), server_default=func.now())
   updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class GeometryRow(Base):
   __tablename__ = "geometries"
   __table_args__ = {'schema': 'web_general'}

   uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
   geometry_name = Column(String, nullable=False)
   created_by = Column(String, default="user")
   system_uuid = Column(String, nullable=True)
   geometry = Column(Geometry(geometry_type='GEOMETRY', srid=4326, spatial_index=True))
   created_at = Column(DateTime(timezone=True), server_default=func.now())
   updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MissionAssetRow(Base):
   """ Junction table connecting teams, missions, rules, and geometries. """
   __tablename__ = "mission_assets"
   __table_args__ = {'schema': 'web_general'}

   uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
   geometry_uuid = Column(UUID(as_uuid=True), nullable=True)
   mission_uuid = Column(UUID(as_uuid=True), nullable=False)
   team_uuid = Column(UUID(as_uuid=True), nullable=False)
   rule_uuid = Column(UUID(as_uuid=True), nullable=True)
   geometry_system_uuid = Column(String, nullable=True)
   created_at = Column(DateTime(timezone=True), server_default=func.now())
   updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# --- MISSIONS SCHEMA ---
class GenericRuleRow(Base):
   __tablename__ = "rules"
   __table_args__ = (
       Index('idx_rules_parameters_gin', 'parameters', postgresql_using='gin'),
       {'schema': 'missions'}
   )

   uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
   mission_uuid = Column(UUID(as_uuid=True), index=True)
   name = Column(String)
   description = Column(String)
   value = Column(String)
   geometry_uuids = Column(ARRAY(UUID(as_uuid=True))) # Kept for future use as requested
   parameters = Column(JSONB, default={})
   created_at = Column(DateTime(timezone=True), server_default=func.now())
   updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())