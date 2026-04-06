import traceback
from fastapi import APIRouter, Depends, HTTPException
from shapely.geometry import Point, Polygon
from geoalchemy2.shape import from_shape
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db_session
from app.db_models import MissionDataRow, GeometryRow, GeometryToTeamRow, TeamRow, QAMissionRow, NewMissionRow
from app.pydantic_schemas import RuleCreate

router = APIRouter(prefix="/api/rules", tags=["Rules"])

@router.get("/")
def get_rules(db: Session = Depends(get_db_session)):
    print('---Getting rules to show---')
    try:
        qa_rules_raw = db.query(QAMissionRow).all()
        nm_rules_raw = db.query(NewMissionRow).all()

        qa_mission = db.query(MissionDataRow).filter(MissionDataRow.mission_name_english == 'qa').first()
        nm_mission = db.query(MissionDataRow).filter(MissionDataRow.mission_name_english == 'new_missions').first()

        all_rules = []

        for q in qa_rules_raw:
            all_rules.append({
                "id": str(q.uuid),
                "name": q.code_name,
                "description": f"QA Check: {q.frequency}",
                "value": f"Checks: {q.checks_amount}, Percent: {q.check_precent}%",
                "geometryIds": [str(g) for g in (q.geometry_uuids or [])],
                "parameters": {
                    "code_name": q.code_name, "frequency": q.frequency, "code_type": q.code_type,
                    "checks_amount": q.checks_amount, "check_precent": q.check_precent
                },
                "missionId": str(qa_mission.uuid) if qa_mission else None
            })

        for n in nm_rules_raw:
            all_rules.append({
                "id": str(n.uuid),
                "name": n.nm_values,
                "description": f"Status: {n.status} | Type: {n.type}",
                "value": f"MPT: {n.mpt_values}",
                "geometryIds": [str(g) for g in (n.geometry_uuids or [])],
                "parameters": {
                    "nm_values": n.nm_values, "status": n.status, "type": n.type,
                    "mpt_values": n.mpt_values, "h_values": n.h_values, "nm_id": n.nm_id
                },
                "missionId": str(nm_mission.uuid) if nm_mission else None
            })

        return all_rules
    except Exception as e:
        print(f"\n---time: {datetime.now()}, Error fetching rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch rules")

@router.post("/")
def create_rule(data: RuleCreate, db: Session = Depends(get_db_session)):
    print(f"\n---Creating rule: {data}---")
    rule = data.rule
    try:
        mission_obj = db.query(MissionDataRow).filter(MissionDataRow.uuid == rule.missionId).first()
        if not mission_obj:
            print(f"\n---time: {datetime.now()}, Error saving rule: Mission not found---")
            raise HTTPException(status_code=404, detail="Mission not found")
        
        mission_name = mission_obj.mission_name_english

        final_geo_ids = [gid for gid in (rule.geometryIds or []) if not gid.startswith('g-')]
        if rule.geometryId and not rule.geometryId.startswith('g-') and rule.geometryId not in final_geo_ids:
            final_geo_ids.append(rule.geometryId)

        geos_to_insert = data.newGeos if data.newGeos else ([data.newGeo] if data.newGeo else [])
        
        for geo in geos_to_insert:
            # SHAPELY INTEGRATION HERE!
            if geo.type == 'Point':
                shapely_geom = Point(geo.coordinates[1], geo.coordinates[0])
            else:
                poly_ring = [[c[1], c[0]] for c in geo.coordinates]
                if poly_ring and poly_ring[0] != poly_ring[-1]:
                    poly_ring.append(poly_ring[0])
                shapely_geom = Polygon(poly_ring)
            
            new_geo = GeometryRow(
                geometry_name=geo.name,
                created_by='user',
                # from_shape converts Shapely polygon memory straight into PostGIS binary
                geometry=from_shape(shapely_geom, srid=4326)
            )
            db.add(new_geo)
            db.flush() 
            
            final_geo_ids.append(str(new_geo.uuid))

            team = db.query(TeamRow).first()
            if team:
                link = GeometryToTeamRow(
                    geometry_uuid=new_geo.uuid,
                    mission_uuid=rule.missionId,
                    team_uuid=team.uuid
                )
                db.add(link)

        params = rule.parameters or {}
        if mission_name == 'qa':
            new_qa = QAMissionRow(
                code_name=params.get('code_name', rule.name),
                frequency=params.get('frequency', rule.description),
                code_type=params.get('code_type', rule.value),
                geometry_uuids=final_geo_ids,
                checks_amount=params.get('checks_amount') if params.get('checks_amount') not in (None, "") else 1,
                check_precent=params.get('check_precent') if params.get('check_precent') not in (None, "") else 100
            )
            db.add(new_qa)
        elif mission_name == 'new_missions':
            new_nm = NewMissionRow(
                nm_values=params.get('nm_values', rule.name),
                status=params.get('status', rule.description),
                type=params.get('type', rule.value),
                geometry_uuids=final_geo_ids,
                h_values=params.get('h_values', 'default'),
                nm_id=params.get('nm_id', 'default'),
                mpt_values=params.get('mpt_values', 'default')
            )
            db.add(new_nm)
        else:
            print(f"\n---time: {datetime.now()}, Error saving rule: Unknown mission type---")
            raise HTTPException(status_code=400, detail=f"Unknown mission type: {mission_name}")
        
        db.commit()
        return {"message": "Rule saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"\n---time: {datetime.now()}, Error saving rule: {e}---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{rule_id}")
def update_rule(rule_id: str, data: RuleCreate, db: Session = Depends(get_db_session)):
    print(f"\n---Updating rule {rule_id}---")
    rule = data.rule
    try:
        mission_obj = db.query(MissionDataRow).filter(MissionDataRow.uuid == rule.missionId).first()
        if not mission_obj:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        mission_name = mission_obj.mission_name_english

        final_geo_ids = [gid for gid in (rule.geometryIds or []) if not gid.startswith('g-')]
        if rule.geometryId and not rule.geometryId.startswith('g-') and rule.geometryId not in final_geo_ids:
            final_geo_ids.append(rule.geometryId)

        geos_to_insert = data.newGeos if data.newGeos else ([data.newGeo] if data.newGeo else [])

        for geo in geos_to_insert:
            # SHAPELY INTEGRATION HERE
            if geo.type == 'Point':
                shapely_geom = Point(geo.coordinates[1], geo.coordinates[0])
            else:
                poly_ring = [[c[1], c[0]] for c in geo.coordinates]
                if poly_ring and poly_ring[0] != poly_ring[-1]:
                    poly_ring.append(poly_ring[0])
                shapely_geom = Polygon(poly_ring)
            
            new_geo = GeometryRow(
                geometry_name=geo.name,
                created_by='user',
                geometry=from_shape(shapely_geom, srid=4326)
            )
            db.add(new_geo)
            db.flush()
            
            final_geo_ids.append(str(new_geo.uuid))

            team = db.query(TeamRow).first()
            if team:
                link = GeometryToTeamRow(
                    geometry_uuid=new_geo.uuid,
                    mission_uuid=rule.missionId,
                    team_uuid=team.uuid
                )
                db.add(link)

        params = rule.parameters or {}
        if mission_name == 'qa':
            qa_rule = db.query(QAMissionRow).filter(QAMissionRow.uuid == rule_id).first()
            if qa_rule:
                qa_rule.code_name = params.get('code_name', rule.name)
                qa_rule.frequency = params.get('frequency', rule.description)
                qa_rule.code_type = params.get('code_type', rule.value)
                qa_rule.geometry_uuids = final_geo_ids
                qa_rule.checks_amount = params.get('checks_amount') if params.get('checks_amount') not in (None, "") else 1
                qa_rule.check_precent = params.get('check_precent') if params.get('check_precent') not in (None, "") else 100
        elif mission_name == 'new_missions':
            nm_rule = db.query(NewMissionRow).filter(NewMissionRow.uuid == rule_id).first()
            if nm_rule:
                nm_rule.nm_values = params.get('nm_values', rule.name)
                nm_rule.status = params.get('status', rule.description)
                nm_rule.type = params.get('type', rule.value)
                nm_rule.geometry_uuids = final_geo_ids
                nm_rule.h_values = params.get('h_values', 'default')
                nm_rule.nm_id = params.get('nm_id', 'default')
                nm_rule.mpt_values = params.get('mpt_values', 'default')
        
        db.commit()
        return {"message": "Rule updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"\n---time: {datetime.now()}, Error updating rule {rule_id}: {e}---")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{rule_id}")
def delete_rule(rule_id: str, db: Session = Depends(get_db_session)):
    print(f"---Deleting rule {rule_id}---")
    try:
        deleted_qa = db.query(QAMissionRow).filter(QAMissionRow.uuid == rule_id).delete()
        deleted_nm = db.query(NewMissionRow).filter(NewMissionRow.uuid == rule_id).delete()
        
        if deleted_qa == 0 and deleted_nm == 0:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        db.commit()
        return {"message": "Rule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n---time: {datetime.now()}, Error deleting rule {rule_id}: {e}---")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete rule")
