"""
Background job management endpoints.
"""
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from ..auth import (
    create_job, get_job, get_user_jobs, update_job_status,
    get_job_result, get_job_result_blob,
)
from .auth_router import get_current_user

router = APIRouter()


class SubmitPDFBody(BaseModel):
    dateOfBirth: str
    timeOfBirth: str
    latitude: float
    longitude: float
    timezone: str
    houseSystem: Optional[str] = "W"
    nodeMode: Optional[str] = "mean"
    clientName: Optional[str] = ""
    reportTitle: Optional[str] = "Vedic Birth Chart Report"
    brandName: Optional[str] = None
    contactMobile: Optional[str] = None
    contactEmail: Optional[str] = None
    contactWebsite: Optional[str] = None


@router.post("/submit-pdf")
def submit_pdf_job(body: SubmitPDFBody, user: dict = Depends(get_current_user)):
    """Submit a PDF generation job to background worker."""
    job = create_job(user["id"], "pdf_generation", body.model_dump())

    try:
        from ..workers.pdf_worker import generate_pdf_task
        task = generate_pdf_task.delay(job["id"])
        update_job_status(job["id"], "pending", celery_task_id=task.id)
    except Exception:
        # If Redis/Celery is not running, generate synchronously
        update_job_status(job["id"], "processing")
        try:
            from ..pdf_generator import KundliPDFGenerator
            from ..auth import store_job_result

            generator = KundliPDFGenerator(
                birth_date=body.dateOfBirth, birth_time=body.timeOfBirth,
                latitude=body.latitude, longitude=body.longitude,
                timezone=body.timezone, house_system=body.houseSystem or "W",
                node_mode=body.nodeMode or "mean",
                client_name=body.clientName or "",
                report_title=body.reportTitle or "Vedic Birth Chart Report",
                brand_name=body.brandName, contact_mobile=body.contactMobile,
                contact_email=body.contactEmail, contact_website=body.contactWebsite,
            )
            pdf_bytes = generator.generate()
            safe_name = (body.clientName or "Report").replace(" ", "_")
            filename = f"{safe_name}_Kundli_Report.pdf"
            store_job_result(job["id"], "pdf", pdf_bytes, filename)
            update_job_status(job["id"], "completed",
                              result_data=json.dumps({"filename": filename, "size": len(pdf_bytes)}))
        except Exception as e:
            update_job_status(job["id"], "failed", error_message=str(e))

    return {
        "job_id": job["id"],
        "status": "pending",
        "message": "PDF generation job submitted. Poll /jobs/{job_id} for status.",
    }


class SubmitAIBody(BaseModel):
    question: str
    dateOfBirth: str
    timeOfBirth: str
    latitude: float
    longitude: float
    timezone: str
    houseSystem: Optional[str] = "W"
    nodeMode: Optional[str] = "mean"
    job_type: Optional[str] = "ai_chat"


@router.post("/submit-ai")
def submit_ai_job(body: SubmitAIBody, user: dict = Depends(get_current_user)):
    """Submit an AI interpretation job to background worker."""
    job = create_job(user["id"], body.job_type, body.model_dump())

    try:
        from ..workers.ai_worker import ai_chat_task, ai_interpretation_task
        if body.job_type == "ai_interpretation":
            task = ai_interpretation_task.delay(job["id"])
        else:
            task = ai_chat_task.delay(job["id"])
        update_job_status(job["id"], "pending", celery_task_id=task.id)
    except Exception:
        # Fallback: try synchronous
        update_job_status(job["id"], "processing")
        try:
            from ..workers.ai_worker import _call_ai_api, _build_ai_context, _detect_topic, _default_model
            from ..auth import get_active_ai_provider
            from ..crypto import decrypt_api_key

            provider_config = get_active_ai_provider(user["id"])
            if not provider_config:
                update_job_status(job["id"], "failed",
                                  error_message="No AI provider configured")
                return {"job_id": job["id"], "status": "failed"}

            api_key = decrypt_api_key(provider_config["api_key_encrypted"])
            provider = provider_config["provider"]
            model = provider_config.get("model") or _default_model(provider)

            chart_context = _build_ai_context(body.model_dump())
            response_text = _call_ai_api(provider, api_key, model,
                                          "You are an expert Vedic astrologer.",
                                          f"Birth Chart:\n{chart_context}\n\nQuestion: {body.question}")

            result = {"answer": response_text, "provider": provider, "model": model, "topic": _detect_topic(body.question)}
            from ..auth import store_job_result
            store_job_result(job["id"], "json", json.dumps(result).encode())
            update_job_status(job["id"], "completed", result_data=json.dumps(result))
        except Exception as e:
            update_job_status(job["id"], "failed", error_message=str(e))

    return {"job_id": job["id"], "status": "pending", "message": "AI job submitted. Poll /jobs/{job_id} for status."}


@router.get("/{job_id}")
def job_status(job_id: int, user: dict = Depends(get_current_user)):
    """Get status of a background job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["user_id"] != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not your job")

    result = {
        "job_id": job["id"],
        "job_type": job["job_type"],
        "status": job["status"],
        "created_at": job["created_at"],
        "started_at": job["started_at"],
        "completed_at": job["completed_at"],
        "error_message": job["error_message"],
    }
    if job["status"] == "completed" and job["result_data"]:
        result["result"] = json.loads(job["result_data"])

    return result


@router.get("/{job_id}/download")
def download_job_result(job_id: int, user: dict = Depends(get_current_user)):
    """Download the result of a completed job (PDF or JSON)."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["user_id"] != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not your job")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job status: {job['status']}")

    job_result = get_job_result(job_id)
    if not job_result:
        raise HTTPException(status_code=404, detail="Result not found")

    blob = get_job_result_blob(job_id)
    if not blob:
        raise HTTPException(status_code=404, detail="Result data not found")

    filename = job_result.get("filename") or f"job_{job_id}_result"

    if job_result["result_type"] == "pdf":
        return Response(
            content=blob,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        return Response(
            content=blob,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


@router.get("")
def my_jobs(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """List current user's jobs."""
    jobs = get_user_jobs(user["id"], status=status, limit=limit)
    return [
        {
            "job_id": j["id"],
            "job_type": j["job_type"],
            "status": j["status"],
            "created_at": j["created_at"],
            "completed_at": j["completed_at"],
            "error_message": j["error_message"],
        }
        for j in jobs
    ]
