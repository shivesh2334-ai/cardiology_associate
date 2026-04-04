"""
AC Agent — Patients Router
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import Patient, PatientStatus, VitalSigns, ICUData, LabResult, Medication, FamilyBriefing
from schemas import (
    PatientCreate, PatientUpdate, PatientOut, PatientListItem,
    VitalsCreate, VitalsOut, ICUDataUpsert, ICUDataOut,
    SuccessResponse
)

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("", response_model=list[PatientListItem])
async def list_patients(
    status: Optional[PatientStatus] = PatientStatus.ACTIVE,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Active patient list for home screen."""
    result = await db.execute(
        select(Patient).where(Patient.status == status).order_by(Patient.admitted_at)
    )
    patients = result.scalars().all()
    now = datetime.now(timezone.utc)

    items = []
    for p in patients:
        admitted = p.admitted_at
        if admitted.tzinfo is None:
            admitted = admitted.replace(tzinfo=timezone.utc)
        days = max(1, (now - admitted).days)

        # Check briefing overdue
        briefing_overdue = False
        if p.next_briefing_due:
            nbd = p.next_briefing_due
            if nbd.tzinfo is None:
                nbd = nbd.replace(tzinfo=timezone.utc)
            briefing_overdue = now > nbd

        items.append(PatientListItem(
            id=p.id,
            uhid=p.uhid,
            full_name=p.full_name,
            age=p.age,
            sex=p.sex,
            ward=p.ward,
            bed_number=p.bed_number,
            primary_diagnosis=p.primary_diagnosis,
            trajectory=p.trajectory,
            admitted_at=p.admitted_at,
            days_admitted=days,
            briefing_overdue=briefing_overdue,
            has_pending_results=False,  # Phase 2: check from results monitor
        ))
    return items


@router.post("", response_model=PatientOut, status_code=201)
async def create_patient(
    body: PatientCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    patient = Patient(**body.model_dump())
    if body.ai_consent:
        patient.ai_consent_at = datetime.now(timezone.utc)
    db.add(patient)
    await db.flush()
    return PatientOut.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientOut.model_validate(patient)


@router.patch("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: uuid.UUID,
    body: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(patient, field, value)
    await db.flush()
    return PatientOut.model_validate(patient)


@router.post("/{patient_id}/vitals", response_model=VitalsOut, status_code=201)
async def add_vitals(
    patient_id: uuid.UUID,
    body: VitalsCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Patient not found")
    v = VitalSigns(patient_id=patient_id, **body.model_dump())
    db.add(v)
    await db.flush()
    return VitalsOut.model_validate(v)


@router.get("/{patient_id}/vitals", response_model=list[VitalsOut])
async def get_vitals(
    patient_id: uuid.UUID,
    limit: int = Query(24, le=100),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(VitalSigns)
        .where(VitalSigns.patient_id == patient_id)
        .order_by(VitalSigns.recorded_at.desc())
        .limit(limit)
    )
    return [VitalsOut.model_validate(v) for v in result.scalars().all()]


@router.put("/{patient_id}/icu", response_model=ICUDataOut)
async def upsert_icu_data(
    patient_id: uuid.UUID,
    body: ICUDataUpsert,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(select(ICUData).where(ICUData.patient_id == patient_id))
    icu = result.scalar_one_or_none()
    if icu:
        for field, value in body.model_dump(exclude_none=True).items():
            setattr(icu, field, value)
    else:
        icu = ICUData(patient_id=patient_id, **body.model_dump())
        db.add(icu)
    await db.flush()
    return ICUDataOut.model_validate(icu)


@router.patch("/{patient_id}/consent", response_model=SuccessResponse)
async def record_ai_consent(
    patient_id: uuid.UUID,
    consent_by: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.ai_consent = True
    patient.ai_consent_by = consent_by
    patient.ai_consent_at = datetime.now(timezone.utc)
    await db.flush()
    return SuccessResponse(message="AI assistance consent recorded")
