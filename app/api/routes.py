# app/api/routes.py
# FULL UPDATED ROUTES WITH LOGGING

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.rag_pipeline import run_rag
from app.services.resume_service import scan_resume
from app.services.roadmap_service import generate_roadmap
from app.utils.logger import logger

router = APIRouter()


# =====================================================
# HEALTH
# =====================================================
@router.get("/health")
async def health():
    logger.info("Health Check Called")

    return {
        "status": "ok",
        "service": "Career AI API"
    }


# =====================================================
# CAREER SEARCH
# =====================================================
@router.post("/career-search")
async def career_search(question: str = Form(...)):

    logger.info(f"Career Search Query: {question}")

    try:
        result = await run_rag(question)

        logger.info("Career Search Success")

        return result

    except Exception as e:

        logger.error(f"Career Search Failed: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Career search failed"
        )


# =====================================================
# RESUME SCAN
# =====================================================
@router.post("/resume-scan")
async def resume_scan_route(
    text: str = Form(None),
    file: UploadFile = File(None)
):

    logger.info("Resume Scan Started")

    try:
        result = await scan_resume(
            text=text,
            file=file
        )

        logger.info("Resume Scan Success")

        return result

    except Exception as e:

        logger.error(f"Resume Scan Failed: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Resume scan failed"
        )


# =====================================================
# CAREER ROADMAP
# =====================================================
@router.post("/career-roadmap")
async def career_roadmap(
    career: str = Form(...)
):

    logger.info(f"Roadmap Request: {career}")

    try:
        result = await generate_roadmap(career)

        logger.info("Roadmap Success")

        return result

    except Exception as e:

        logger.error(f"Roadmap Failed: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Roadmap generation failed"
        )