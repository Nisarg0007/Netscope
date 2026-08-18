from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import SessionLocal
from app.models.history import NetworkHistory
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=dict)
def get_history(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of snapshots to return"),
    start_time: Optional[str] = Query(None, description="Start time in ISO format (inclusive)"),
    end_time: Optional[str] = Query(None, description="End time in ISO format (inclusive)")
):
    """
    Get historical network snapshots.
    """
    db = SessionLocal()
    try:
        query = db.query(NetworkHistory)

        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                query = query.filter(NetworkHistory.timestamp >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO format.")

        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time)
                query = query.filter(NetworkHistory.timestamp <= end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format. Use ISO format.")

        # Order by timestamp descending (most recent first) and then limit
        query = query.order_by(desc(NetworkHistory.timestamp))
        results = query.limit(limit).all()

        # Convert to list of dictionaries
        snapshots = [record.to_dict() for record in results]

        return {
            "snapshots": snapshots,
            "count": len(snapshots)
        }
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()

@router.get("/latest", response_model=dict)
def get_latest_history():
    """
    Get the most recent historical snapshot.
    """
    db = SessionLocal()
    try:
        record = db.query(NetworkHistory).order_by(desc(NetworkHistory.timestamp)).first()
        if record is None:
            return {
                "snapshots": [],
                "count": 0
            }
        return {
            "snapshots": [record.to_dict()],
            "count": 1
        }
    except Exception as e:
        logger.error(f"Error retrieving latest history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()

@router.delete("/", response_model=dict)
def clear_history():
    """
    Clear all historical snapshots.
    """
    db = SessionLocal()
    try:
        db.query(NetworkHistory).delete()
        db.commit()
        return {
            "message": "History cleared successfully",
            "count": 0
        }
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()