"""H38 — GET /weekly-reports/{report_id}/export?kind=aggregate|case&episode_id=.

No bulk-identifiable endpoint exists in this router — `kind=case` always
resolves exactly one durable episode, gated by `can_access_case`.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.auth.principal import Principal, require_active_role
from app.auth.rbac import audit
from app.weekly.export import (
    ExportError,
    export_aggregate_csv,
    export_case,
    export_case_csv,
    validate_export_kind,
)
from app.weekly.state import case_repository, get_report
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/weekly-reports", tags=["weekly-reports"])

_ERROR_STATUS = {
    "invalid_kind": 400,
    "missing_episode_id": 400,
    "not_found": 404,
    "forbidden": 403,
}


@router.get("/{report_id}/export")
def export_weekly_report(
    report_id: str,
    kind: str = Query(...),
    episode_id: Optional[str] = Query(default=None),
    principal: Principal = Depends(require_active_role),
    db: Session = Depends(get_db),
) -> Response:
    try:
        validate_export_kind(kind, episode_id=episode_id)
    except ExportError as err:
        audit(
            principal,
            action=f"export.{kind}",
            resource_handle=report_id,
            allowed=False,
            db=db,
        )
        raise HTTPException(
            status_code=_ERROR_STATUS.get(err.code, 400),
            detail={"code": err.code, "message": str(err)},
        ) from err

    if kind == "aggregate":
        report = get_report(report_id)
        if report is None:
            audit(
                principal,
                action="export.aggregate",
                resource_handle=report_id,
                allowed=False,
                db=db,
            )
            raise HTTPException(
                status_code=404, detail={"code": "not_found", "message": "report not found"}
            )
        csv_body = export_aggregate_csv(report)
        filename = f"{report_id}-aggregate.csv"
    else:
        try:
            result = export_case(case_repository, episode_id or "", principal)
        except ExportError as err:
            audit(
                principal,
                action="export.case",
                resource_handle=episode_id or report_id,
                allowed=False,
                db=db,
            )
            raise HTTPException(
                status_code=_ERROR_STATUS.get(err.code, 400),
                detail={"code": err.code, "message": str(err)},
            ) from err
        csv_body = export_case_csv(result)
        filename = f"{report_id}-{result.episode_id}.csv"

    audit(
        principal,
        action=f"export.{kind}",
        resource_handle=report_id if kind == "aggregate" else (episode_id or report_id),
        allowed=True,
        db=db,
    )
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
