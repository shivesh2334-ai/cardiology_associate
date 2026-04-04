"""
AC Agent — Briefings Router
"""
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import FamilyBriefing
from schemas import (
    BriefingInputPayload, BriefingGenerateResponse,
    BriefingCompleteRequest, BriefingOut
)
from services.briefing_service import generate_briefing, complete_briefing

router = APIRouter(prefix="/briefings", tags=["Family Briefings"])


@router.post("/generate", response_model=BriefingGenerateResponse, status_code=201)
async def generate(
    payload: BriefingInputPayload,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate AI family briefing document. Returns structured briefing for co-pilot screen."""
    return await generate_briefing(payload, db)


@router.post("/complete", response_model=BriefingOut)
async def complete(
    request: BriefingCompleteRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """File the completed family briefing log after the meeting."""
    return await complete_briefing(request, user.id, db)


@router.get("/patient/{patient_id}", response_model=list[BriefingOut])
async def list_patient_briefings(
    patient_id: uuid.UUID,
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(FamilyBriefing)
        .where(FamilyBriefing.patient_id == patient_id)
        .order_by(FamilyBriefing.created_at.desc())
        .limit(limit)
    )
    return [BriefingOut.model_validate(b) for b in result.scalars().all()]
