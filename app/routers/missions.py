# -- scripts imports --
from app.database import get_db_session
from app.db_models import MissionDataRow
# -- env imports --
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter(prefix="/api/missions", tags=["Missions"])

@router.get("/")
def get_missions(db: Session = Depends(get_db_session)):
    print("\n---Getting missions to show---")
    try:
        missions = db.query(MissionDataRow).all()
        return [
            {
                "id": str(m.uuid),
                "name": m.mission_name_english,
                "nameHebrew": m.mission_name_hebrew,
                "description": ""
            }
            for m in missions
        ]
    except Exception as e:
        print(f"\n---time: {datetime.now()}, Error fetching missions: {e}---")
        raise HTTPException(status_code=500, detail="Failed to fetch missions")
