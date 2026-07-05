from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, manager_or_admin
from app.models.user import User
from app.services.alerts import run_alert_scan

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/run")
def run_scan(
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> dict[str, int]:
    """On-demand trigger of the predictive alert scan (rule 2.2)."""
    return {"created": run_alert_scan(db)}
