# -- scripts imports --
from app.db_models import MissionDataRow, GeometryRow, GeometryToTeamRow, TeamRow, GenericRuleRow
from app.pydantic_schemas import RuleCreate
from app.database import get_db_session
# -- env imports --
from fastapi import APIRouter, Depends, HTTPException
from shapely.geometry import Point, Polygon
from geoalchemy2.shape import from_shape
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/rules", tags=["Rules"])


def _process_geometries(rule_data, geos_data, db: Session):
    # Start with existing geometries that WERE NOT part of the "edit" batch
    # (Filtering out 'g-' temporary frontend IDs)
    final_geo_ids = [gid for gid in (rule_data.geometryIds or []) if not str(gid).startswith('g-')]

    for geo in geos_data:
        # A. Create the spatial shape (Point/Polygon)
        if geo.type == 'Point':
            shapely_geom = Point(geo.coordinates[1], geo.coordinates[0])
        else:
            poly_ring = [[c[1], c[0]] for c in geo.coordinates]
            if poly_ring and poly_ring[0] != poly_ring[-1]:
                poly_ring.append(poly_ring[0])
            shapely_geom = Polygon(poly_ring)
        # B. Check if this geometry already exists in your DB
        # getattr is used here to safely check for 'id' without crashing
        if geo.id and not str(geo.id).startswith('g-'):
            # --- PATH 1: UPDATE EXISTING ---
            geo_row = db.query(GeometryRow).filter(GeometryRow.uuid == geo.id).first()
            if geo_row:
                # the update !!
                geo_row.geometry_name = geo.name
                geo_row.geometry = from_shape(shapely_geom, srid=4326)

                # Ensure the ID is in our final list
                if str(geo_row.uuid) not in final_geo_ids:
                    final_geo_ids.append(str(geo_row.uuid))
                continue  # Done with this one, move to next
        # --- PATH 2: if the geometry does not exist add new mission ---
        # (If no ID provided, or the ID wasn't found in the DB)
        new_geo = GeometryRow(geometry_name=geo.name, created_by='user', geometry=from_shape(shapely_geom, srid=4326))
        db.add(new_geo)
        db.flush()  # Generate the UUID
        final_geo_ids.append(str(new_geo.uuid))

        # Link to team (only needed for new geometries)
        team = db.query(TeamRow).first()
        if team:
            db.add(GeometryToTeamRow(geometry_uuid=new_geo.uuid, mission_uuid=rule_data.missionId, team_uuid=team.uuid))
    return final_geo_ids


def _process_rule_creation(data: RuleCreate, db: Session):
    mission_obj = db.query(MissionDataRow).filter(MissionDataRow.uuid == data.rule.missionId).first()
    if not mission_obj:
        print(f"\n---time: {datetime.now()}, Error saving rule: Mission not found---")
        raise HTTPException(status_code=404, detail="Mission not found")
    geos_to_insert = data.newGeos if data.newGeos else ([data.newGeo] if data.newGeo else [])
    final_geo_ids = _process_geometries(data.rule, geos_to_insert, db)
    # 100% Generic Insertion! Dump the entire parameters dict raw into the database row!
    new_rule = GenericRuleRow(
        mission_uuid=data.rule.missionId,
        name=data.rule.name,
        description=data.rule.description,
        value=data.rule.value,
        geometry_uuids=final_geo_ids,
        parameters=data.rule.parameters or {}
    )
    db.add(new_rule)


def _process_rule_update(rule_id: str, data: RuleCreate, db: Session):
    rule_row = db.query(GenericRuleRow).filter(GenericRuleRow.uuid == rule_id).first()
    if not rule_row:
        raise HTTPException(status_code=404, detail="Rule not found")
    geos_to_insert = data.newGeos if data.newGeos else ([data.newGeo] if data.newGeo else [])
    final_geo_ids = _process_geometries(data.rule, geos_to_insert, db)
    # Completely agnostic parameter overwrite!
    rule_row.name = data.rule.name
    rule_row.description = data.rule.description
    rule_row.value = data.rule.value
    rule_row.geometry_uuids = final_geo_ids
    rule_row.parameters = data.rule.parameters or {}


@router.get("/")
def get_rules(db: Session = Depends(get_db_session)):
    try:
        rules_raw = db.query(GenericRuleRow).all()
        all_rules = []
        for r in rules_raw:
            all_rules.append({
                "id": str(r.uuid),
                "name": r.name,
                "description": r.description,
                "value": r.value,
                "geometryIds": [str(g) for g in (r.geometry_uuids or [])],
                "parameters": r.parameters,
                "missionId": str(r.mission_uuid) if r.mission_uuid else None
            })
        return all_rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch rules {e}")


@router.post("/create-rule")
def create_rule(data: RuleCreate, db: Session = Depends(get_db_session)):
    # logger
    try:
        _process_rule_creation(data, db)
        db.commit()
        return {"message": "Rule saved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update-rule-{rule_id}")
def update_rule(rule_id: str, data: RuleCreate, db: Session = Depends(get_db_session)):
    try:
        _process_rule_update(rule_id, data, db)
        db.commit()
        return {"message": "Rule updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-rule-{rule_id}")
def delete_rule(rule_id: str, db: Session = Depends(get_db_session)):
    try:
        deleted = db.query(GenericRuleRow).filter(GenericRuleRow.uuid == rule_id).delete()
        if deleted == 0: raise HTTPException(status_code=404, detail="Rule not found")
        db.commit()
        return {"message": "Rule deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete rule")


# NOT IN USE FOR NOW !!
@router.post("/bulk")
def bulk_create_rules(items: List[RuleCreate], db: Session = Depends(get_db_session)):
    try:
        for data in items: _process_rule_creation(data, db)
        db.commit()
        return {"message": f"Successfully processed items"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/bulk")
def bulk_update_rules(items: List[RuleCreate], db: Session = Depends(get_db_session)):
    try:
        for data in items: _process_rule_update(data.rule.id, data, db)
        db.commit()
        return {"message": f"Successfully updated items"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))