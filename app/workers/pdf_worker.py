"""
PDF generation Celery tasks.
"""
import json
import logging
from ..celery_app import celery_app
from ..auth import update_job_status, create_job, store_job_result

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.pdf_worker.generate_pdf", bind=True, max_retries=2)
def generate_pdf_task(self, job_id: int):
    """Generate a full Kundli PDF report in background."""
    try:
        from ..auth import get_job
        from ..pdf_generator import KundliPDFGenerator

        job = get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        update_job_status(job_id, "processing")
        input_data = json.loads(job["input_data"])

        generator = KundliPDFGenerator(
            birth_date=input_data["dateOfBirth"],
            birth_time=input_data["timeOfBirth"],
            latitude=input_data["latitude"],
            longitude=input_data["longitude"],
            timezone=input_data["timezone"],
            house_system=input_data.get("houseSystem", "W"),
            node_mode=input_data.get("nodeMode", "mean"),
            client_name=input_data.get("clientName", ""),
            report_title=input_data.get("reportTitle", "Vedic Birth Chart Report"),
            brand_name=input_data.get("brandName"),
            contact_mobile=input_data.get("contactMobile"),
            contact_email=input_data.get("contactEmail"),
            contact_website=input_data.get("contactWebsite"),
        )

        pdf_bytes = generator.generate()
        safe_name = (input_data.get("clientName") or "Report").replace(" ", "_")
        filename = f"{safe_name}_Kundli_Report.pdf"

        store_job_result(job_id, "pdf", pdf_bytes, filename)

        update_job_status(
            job_id, "completed",
            result_data=json.dumps({
                "filename": filename,
                "size": len(pdf_bytes),
                "sections": 22,
            }),
        )
        logger.info(f"PDF job {job_id} completed: {filename} ({len(pdf_bytes)} bytes)")

    except Exception as e:
        logger.exception(f"PDF job {job_id} failed")
        update_job_status(job_id, "failed", error_message=str(e))


@celery_app.task(name="app.workers.pdf_worker.generate_pdf_batch")
def generate_pdf_batch_task(job_ids: list):
    """Generate multiple PDFs in batch."""
    for job_id in job_ids:
        generate_pdf_task.delay(job_id)
