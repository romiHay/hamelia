# -- scripts imports --
from app.db_models import GeometryRow, GeometryToTeamRow, QAMissionRow, NewMissionRow
from app.database import get_db_session
from sqlalchemy.orm import Session
# -- env imports --
from fastapi import APIRouter, Depends, HTTPException, Body
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from datetime import datetime

router = APIRouter(prefix="/api/geometries", tags=["Geometries"])

@router.get("/")
def get_geometries(db: Session = Depends(get_db_session)):
    print("\n---Getting geometries to show---")
    try:
        results = db.query(
            GeometryRow.uuid,
            GeometryRow.geometry_name,
            GeometryRow.created_by,
            GeometryRow.geometry, 
            GeometryToTeamRow.mission_uuid
        ).outerjoin(
            GeometryToTeamRow, GeometryRow.uuid == GeometryToTeamRow.geometry_uuid
        ).all()

        formatted = []
        for row in results:
            if row.geometry is None:
                continue
            
            # Converts binary WKB from the database directly into a Shapely object
            shapely_geom = to_shape(row.geometry)
            # mapping() neatly turns Shapely shapes into GeoJSON dicts
            geo = mapping(shapely_geom)
            
            coords = geo['coordinates']
            
            if geo['type'] == 'Point':
                coords = [coords[1], coords[0]]
            elif geo['type'] == 'Polygon':
                coords = [[c[1], c[0]] for c in coords[0]]
                
            qa_match = db.query(QAMissionRow.uuid).filter(
                QAMissionRow.geometry_uuids.any(str(row.uuid))
            ).first()
            
            nm_match = db.query(NewMissionRow.uuid).filter(
                NewMissionRow.geometry_uuids.any(str(row.uuid))
            ).first()

            rule_id = str(qa_match.uuid) if qa_match else (str(nm_match.uuid) if nm_match else None)

            formatted.append({
                "id": str(row.uuid),
                "name": row.geometry_name,
                "missionId": str(row.mission_uuid) if row.mission_uuid else None,
                "type": geo['type'],
                "coordinates": coords,
                "ruleId": rule_id,
                "createdBy": row.created_by
            })
        return formatted
    except Exception as e:
        print(f"\n---time: {datetime.now()}, Error fetching geometries: {e}---")
        raise HTTPException(status_code=500, detail="Failed to fetch geometries")

@router.post("/bulk-delete")
def bulk_delete_geometries(geo_ids: list[str] = Body(...), db: Session = Depends(get_db_session)):
    print(f"\n---bulk_delete_geometries: {geo_ids}---")
    try:
        db.query(GeometryToTeamRow).filter(GeometryToTeamRow.geometry_uuid.in_(geo_ids)).delete(synchronize_session=False)
        deleted = db.query(GeometryRow).filter(
            GeometryRow.uuid.in_(geo_ids), 
            GeometryRow.created_by == 'user'
        ).delete(synchronize_session=False)
        
        db.commit()
        return {"message": f"Successfully deleted {deleted} geometries"}
    except Exception as e:
        db.rollback()
        print(f"\n---time: {datetime.now()}, Error bulk deleting geometries {geo_ids}: {e}---")
        raise HTTPException(status_code=500, detail="Failed to bulk delete geometries")

@router.delete("/{geo_id}")
def delete_geometry(geo_id: str, db: Session = Depends(get_db_session)):
    print(f"\n---Deleting geometry {geo_id}---")
    try:
        db.query(GeometryToTeamRow).filter(GeometryToTeamRow.geometry_uuid == geo_id).delete(synchronize_session=False)
        deleted = db.query(GeometryRow).filter(
            GeometryRow.uuid == geo_id,
            GeometryRow.created_by == 'user'
        ).delete(synchronize_session=False)
        
        if deleted == 0:
            db.rollback()
            raise HTTPException(status_code=404, detail="Geometry not found or cannot be deleted")
            
        db.commit()
        return {"message": "Geometry deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n---time: {datetime.now()}, Error deleting geometry {geo_id}: {e}---")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete geometry")
