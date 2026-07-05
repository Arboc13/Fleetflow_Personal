import datetime as dt
from typing import Literal

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.deps import get_db, manager_or_admin
from app.models.user import User
from app.schemas.report import TCOReport
from app.services.report import tco_report
from app.services.report_export import tco_to_pdf, tco_to_xlsx

router = APIRouter(prefix="/reports", tags=["reports"])

_MEDIA_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


@router.get("/tco", response_model=TCOReport)
def get_tco_report(
    date_from: dt.date,
    date_to: dt.date,
    vehicle_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> TCOReport:
    return tco_report(db, date_from=date_from, date_to=date_to, vehicle_id=vehicle_id)


@router.get("/tco/export")
def export_tco_report(
    date_from: dt.date,
    date_to: dt.date,
    format: Literal["xlsx", "pdf"] = "xlsx",
    vehicle_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> Response:
    report = tco_report(db, date_from=date_from, date_to=date_to, vehicle_id=vehicle_id)
    content = tco_to_xlsx(report) if format == "xlsx" else tco_to_pdf(report)
    filename = f"tco_{date_from}_{date_to}.{format}"
    return Response(
        content=content,
        media_type=_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
