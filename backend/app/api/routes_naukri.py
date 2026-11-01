from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from app.services.naukri_adapter import naukri_adapter
from app.services.naukri_discovery_service import naukri_discovery_service
from app.services.naukri_profile_service import naukri_profile_service
from app.services.naukri_neo_service import naukri_neo_service

router = APIRouter(prefix="/naukri", tags=["Naukri.com Integration & Neo Tracking"])

class ImportUrlRequest(BaseModel):
    url: str
    custom_title: Optional[str] = None
    custom_company: Optional[str] = None

class NeoSettingsRequest(BaseModel):
    is_neo_enabled: bool
    is_naukri360_pro: bool = False

@router.get("/capabilities")
def get_capabilities():
    return naukri_adapter.get_capabilities()

@router.get("/health")
def get_health():
    return naukri_adapter.get_integration_health()

@router.post("/import-url")
def import_url(req: ImportUrlRequest):
    res = naukri_discovery_service.ingest_naukri_url(req.url)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/jobs/{job_id}/prepare")
def prepare_job(job_id: int):
    pkg = naukri_adapter.create_application_package(job_id)
    if not pkg.get("success"):
        raise HTTPException(status_code=404, detail=pkg.get("message"))
    return pkg

@router.post("/batch/prepare")
def prepare_batch(size: int = Query(10), min_score: int = Query(85)):
    return naukri_discovery_service.prepare_naukri_batch(batch_size=size, min_match_score=min_score)

@router.get("/profile-package")
def get_profile_package():
    return naukri_profile_service.generate_profile_optimization_package()

@router.get("/neo/settings")
def get_neo_settings():
    from app.core.database import SessionLocal
    from app.models.schema import NaukriIntegrationSetting
    db = SessionLocal()
    try:
        cfg = db.query(NaukriIntegrationSetting).first()
        return {
            "is_neo_enabled": cfg.is_neo_enabled if cfg else False,
            "is_naukri360_pro": cfg.is_naukri360_pro if cfg else False
        }
    finally:
        db.close()

@router.put("/neo/settings")
def update_neo_settings(req: NeoSettingsRequest):
    return naukri_neo_service.configure_neo(
        is_neo_enabled=req.is_neo_enabled,
        is_naukri360_pro=req.is_naukri360_pro
    )

@router.get("/neo/records")
def get_neo_records(limit: int = Query(20)):
    return {"records": naukri_neo_service.list_neo_applications(limit=limit)}

@router.post("/sync")
def sync_naukri():
    return naukri_adapter.reconcile_application_history()
