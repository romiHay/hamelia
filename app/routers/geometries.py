# -- scripts imports --
from app.db_models import GeometryRow, GeometryToTeamRow, GenericRuleRow
from app.database import get_db_session
# -- env imports --
from fastapi import APIRouter, Depends, HTTPException, Body
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import text

router = APIRouter(prefix="/api/geometries", tags=["Geometries"])


@router.get("/")
def get_geometries(db: Session = Depends(get_db_session)):
    try:
        # SUPER FAST: Database queries
        geos_raw = db.query(GeometryRow).all()
        rules_raw = db.query(GenericRuleRow).all()

        # Query the junction table to get the geometry -> mission mapping directly
        # You can also use your SQLAlchemy model here if you have one, e.g., db.query(GeometryToTeamRow).all()
        geo_to_team_raw = db.execute(
            text("SELECT geometry_uuid, mission_uuid FROM web_general.geometry_to_team")).fetchall()

        # Create an instant-lookup dictionary for Geometry UUID -> Mission UUID
        geo_to_mission_map = {}
        for row in geo_to_team_raw:
            # row[0] is geometry_uuid, row[1] is mission_uuid
            geo_to_mission_map[str(row[0])] = str(row[1])
        # Build an instant-lookup dictionary in Python memory mapping Geo UUID -> Rule Row
        geo_to_rule_map = {}
        for rule in rules_raw:
            for geo_uuid in (rule.geometry_uuids or []):
                geo_to_rule_map[str(geo_uuid)] = rule

        all_geos = []
        for g in geos_raw:
            # Instant memory lookup instead of a slow database query!
            attached_rule = geo_to_rule_map.get(str(g.uuid))
            geo_id_str = str(g.uuid)
            mission_id = geo_to_mission_map.get(geo_id_str)
            if not mission_id and attached_rule:
                mission_id = str(attached_rule.mission_uuid)

            shapely_geom = to_shape(g.geometry)
            if shapely_geom.geom_type == 'Point':
                coords = [shapely_geom.y, shapely_geom.x]
                geo_type = 'Point'
            else:
                coords = [[lat, lon] for lon, lat in shapely_geom.exterior.coords]
                geo_type = 'Polygon'

            all_geos.append({
                "id": geo_id_str,
                "name": g.geometry_name,
                "type": geo_type,
                "coordinates": coords,
                "createdBy": g.created_by,
                "ruleId": str(attached_rule.uuid) if attached_rule else None,
                "missionId": mission_id  # Uses the new mission_id we found above!
            })
        return all_geos
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch geometries")

@router.delete("/bulk-delete-geometries")
def bulk_delete_geometries(geo_ids: list[str], db: Session = Depends(get_db_session)):
    try:
        for geo_id in geo_ids:
            # FIX: Use PostgreSQL .contains() list for Arrays
            attached_rule = db.query(GenericRuleRow).filter(
                GenericRuleRow.geometry_uuids.contains([geo_id])
            ).first()
            if attached_rule:
                e = f"Geometry '{geo_id}' cannot be deleted because it is still attached to rule '{attached_rule.name}'"
                raise HTTPException(status_code=400, detail=e)
            # Cleanup Foreign Keys (Team Link) FIRST
            db.query(GeometryToTeamRow).filter(
                GeometryToTeamRow.geometry_uuid == geo_id
            ).delete(synchronize_session=False)
            # Cleanup Root Geometry
            db.query(GeometryRow).filter(
                GeometryRow.uuid == geo_id
            ).delete(synchronize_session=False)
        db.commit()
        return {"message": f"Successfully deleted {len(geo_ids)} standalone geometries"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-geometry-{geo_id}")
def delete_geometry(geo_id: str, db: Session = Depends(get_db_session)):
    try:
        # FIX: Use PostgreSQL .contains() list for Arrays
        attached_rule = db.query(GenericRuleRow).filter(
            GenericRuleRow.geometry_uuids.contains([geo_id])
        ).first()
        if attached_rule:
            e = f"Geometry cannot be deleted because it is still attached to rule '{attached_rule.name}'"
            raise HTTPException(status_code=400, detail=e)
        # Cleanup Foreign Keys (Team Link) FIRST
        db.query(GeometryToTeamRow).filter(
            GeometryToTeamRow.geometry_uuid == geo_id
        ).delete(synchronize_session=False)
        # Cleanup Root Geometry
        deleted_count = db.query(GeometryRow).filter(
            GeometryRow.uuid == geo_id
        ).delete(synchronize_session=False)
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Geometry not found")
        db.commit()
        return {"message": "Geometry deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
