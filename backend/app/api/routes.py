from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import HistoryPoint, SpotStatus
from app.service import get_spot_history, get_spot_status
from app.spots import load_spot, load_spots

router = APIRouter(prefix="/api")


@router.get("/spots", response_model=list[SpotStatus])
def list_spots(db: Session = Depends(get_db)):
    return [get_spot_status(db, spot) for spot in load_spots()]


@router.get("/spots/{spot_id}", response_model=SpotStatus)
def get_spot(spot_id: str, db: Session = Depends(get_db)):
    spot = load_spot(spot_id)
    if spot is None:
        raise HTTPException(status_code=404, detail=f"Unknown spot '{spot_id}'")
    return get_spot_status(db, spot)


@router.get("/spots/{spot_id}/history", response_model=list[HistoryPoint])
def get_history(spot_id: str, hours: int = Query(default=72, ge=1, le=45 * 24), db: Session = Depends(get_db)):
    spot = load_spot(spot_id)
    if spot is None:
        raise HTTPException(status_code=404, detail=f"Unknown spot '{spot_id}'")
    return get_spot_history(db, spot, hours)
