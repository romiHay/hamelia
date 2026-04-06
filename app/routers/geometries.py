# -- scripts imports --
from app.db_models import GeometryRow, GeometryToTeamRow, GenericRuleRow
from app.database import get_db_session
from sqlalchemy.orm import Session
# -- env imports --
from fastapi import APIRouter, Depends, HTTPException, Body
from geoalchemy2.shape import to_shape
from datetime import datetime

router = APIRouter(prefix="/api/geometries", tags=["Geometries"])


@router.get("/")
def get_geometries(db: Session = Depends(get_db_session)):
    print("\n---Getting geometries to show---")
    try:
        # SUPER FAST: Only 2 Database queries total!
        geos_raw = db.query(GeometryRow).all()
        rules_raw = db.query(GenericRuleRow).all()
        # Build an instant-lookup dictionary in Python memory mapping Geo UUID -> Rule Row
        geo_to_rule_map = {}
        for rule in rules_raw:
            for geo_uuid in (rule.geometry_uuids or []):
                geo_to_rule_map[str(geo_uuid)] = rule
        all_geos = []
        for g in geos_raw:
            # Instant memory lookup instead of a slow database query!
            attached_rule = geo_to_rule_map.get(str(g.uuid))
            shapely_geom = to_shape(g.geometry)
            if shapely_geom.geom_type == 'Point':
                coords = [shapely_geom.y, shapely_geom.x]
                geo_type = 'Point'
            else:
                coords = [[lat, lon] for lon, lat in shapely_geom.exterior.coords]
                geo_type = 'Polygon'
            all_geos.append({
                "id": str(g.uuid),
                "name": g.geometry_name,
                "type": geo_type,
                "coordinates": coords,
                "createdBy": g.created_by,
                "ruleId": str(attached_rule.uuid) if attached_rule else None,
                "missionId": str(attached_rule.mission_uuid) if attached_rule else None
            })
        return all_geos
    except Exception as e:
        print(f"\n---time: {datetime.now()}, Error fetching geometries: {e}---")
        raise HTTPException(status_code=500, detail="Failed to fetch geometries")


@router.delete("/bulk-delete")
def bulk_delete_geometries(geo_ids: list[str], db: Session = Depends(get_db_session)):
    print(f"\n---bulk_delete_geometries: {geo_ids}---")
    try:
        for geo_id in geo_ids:
            # FIX: Use PostgreSQL .contains() list for Arrays
            attached_rule = db.query(GenericRuleRow).filter(
                GenericRuleRow.geometry_uuids.contains([geo_id])
            ).first()
            if attached_rule:
                e = f"Geometry '{geo_id}' cannot be deleted because it is still attached to rule '{attached_rule.name}'"
                print(f"\n---time: {datetime.now()}, Error bulk deleting geometries {geo_ids}: {e}---")
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
        print(f"\n---time: {datetime.now()}, Managed bulk deleting geometries {geo_ids}---")
        return {"message": f"Successfully deleted {len(geo_ids)} standalone geometries"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n---time: {datetime.now()}, Error bulk deleting geometries {geo_ids}: {e}---")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{geo_id}")
def delete_geometry(geo_id: str, db: Session = Depends(get_db_session)):
    print(f"\n---Deleting geometry {geo_id}---")
    try:
        # FIX: Use PostgreSQL .contains() list for Arrays
        attached_rule = db.query(GenericRuleRow).filter(
            GenericRuleRow.geometry_uuids.contains([geo_id])
        ).first()
        if attached_rule:
            e = f"Geometry cannot be deleted because it is still attached to rule '{attached_rule.name}'"
            print(f"\n---time: {datetime.now()}, Error deleting geometry {geo_id}: {e}---")
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
            print(f"\n---time: {datetime.now()}, Error deleting geometry {geo_id}: Geometry not found---")
            raise HTTPException(status_code=404, detail="Geometry not found")
        db.commit()
        print(f"\n---time: {datetime.now()}, Managed deleting geometries {geo_id}---")
        return {"message": "Geometry deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n---time: {datetime.now()}, Error deleting geometry {geo_id}: {e}---")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
