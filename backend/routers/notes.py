"""
AC Agent — Notes Router
"""
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import ClinicalNote
from schemas import (
    NoteInputPayload, NoteGenerateResponse,
    NoteApproveRequest, NoteOut
)
from services.notes_service import generate_note, approve_note, generate_discharge_summary

router = APIRouter(prefix="/notes", tags=["Clinical Notes"])


@router.post("/generate", response_model=NoteGenerateResponse, status_code=201)
async def generate(
    payload: NoteInputPayload,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate AI SOAP note. Returns draft for Associate review."""
    return await generate_note(payload, user.id, db)


@router.post("/approve", response_model=NoteOut)
async def approve(
    request: NoteApproveRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Approve and file a note. Associate may submit edits before approving."""
    return await approve_note(request, user, db)


@router.post("/discharge/{patient_id}", response_model=NoteGenerateResponse, status_code=201)
async def discharge_summary(
    patient_id: uuid.UUID,
    discharge_data: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate discharge summary from all admission notes."""
    return await generate_discharge_summary(patient_id, user.id, discharge_data, db)


@router.get("/patient/{patient_id}", response_model=list[NoteOut])
async def list_patient_notes(
    patient_id: uuid.UUID,
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(ClinicalNote)
        .where(ClinicalNote.patient_id == patient_id)
        .order_by(ClinicalNote.created_at.desc())
        .limit(limit)
    )
    return [NoteOut.model_validate(n) for n in result.scalars().all()]
