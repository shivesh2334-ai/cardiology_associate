"""
AC Agent — Family Briefing Service
Orchestrates briefing generation, storage, and completion.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Patient, FamilyBriefing, BriefingStatus, ClinicalTrajectory
from schemas import (
    BriefingInputPayload, BriefingGenerateResponse, BriefingDocument,
    BriefingCompleteRequest, BriefingOut
)
from services.claude_service import call_claude_json
from prompts.family_briefing import (
    BRIEFING_SYSTEM_PROMPT,
    build_briefing_user_prompt,
    get_specialty_supplement,
)

logger = logging.getLogger(__name__)


def _patient_to_context(patient: Patient, days_admitted: int) -> dict:
    return {
        "full_name": patient.full_name,
        "age": patient.age,
        "sex": patient.sex,
        "uhid": patient.uhid,
        "admitted_at": patient.admitted_at.strftime("%d %b %Y"),
        "days_admitted": days_admitted,
        "ward": patient.ward,
        "bed_number": patient.bed_number,
        "primary_diagnosis": patient.primary_diagnosis,
        "attending_consultant": patient.attending_consultant,
    }


def _days_admitted(patient: Patient) -> int:
    now = datetime.now(timezone.utc)
    admitted = patient.admitted_at
    if admitted.tzinfo is None:
        admitted = admitted.replace(tzinfo=timezone.utc)
    return max(1, (now - admitted).days)


def _calculate_next_briefing(trajectory: ClinicalTrajectory) -> datetime:
    """Next briefing due based on trajectory severity."""
    now = datetime.now(timezone.utc)
    hours_map = {
        ClinicalTrajectory.CRITICAL:      settings.BRIEFING_OVERDUE_HOURS_CRITICAL,
        ClinicalTrajectory.DETERIORATING: settings.BRIEFING_OVERDUE_HOURS_CRITICAL,
        ClinicalTrajectory.GUARDED:       settings.BRIEFING_OVERDUE_HOURS_GUARDED,
        ClinicalTrajectory.STABLE:        settings.BRIEFING_OVERDUE_HOURS_STABLE,
        ClinicalTrajectory.IMPROVING:     settings.BRIEFING_OVERDUE_HOURS_STABLE,
    }
    return now + timedelta(hours=hours_map.get(trajectory, 12))


async def generate_briefing(
    payload: BriefingInputPayload,
    conducted_by_id: uuid.UUID,
    db: AsyncSession,
) -> BriefingGenerateResponse:
    """
    Main service method:
    1. Load patient
    2. Build prompts
    3. Call Claude
    4. Validate response
    5. Store briefing record
    6. Return structured response
    """

    # ── 1. Load patient ───────────────────────────────────────────────────────
    result = await db.execute(select(Patient).where(Patient.id == payload.patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if not patient.ai_consent:
        raise HTTPException(
            status_code=403,
            detail="AI assistance consent not obtained for this patient. Please obtain and record consent first."
        )

    days = _days_admitted(patient)
    patient_context = _patient_to_context(patient, days)

    # ── 2. Build prompts ──────────────────────────────────────────────────────
    specialty_supplement = get_specialty_supplement(patient.primary_diagnosis or "")
    system_prompt = BRIEFING_SYSTEM_PROMPT
    if specialty_supplement:
        system_prompt = system_prompt + "\n\n" + specialty_supplement

    user_prompt = build_briefing_user_prompt(payload, patient_context)

    # ── 3. Call Claude ────────────────────────────────────────────────────────
    raw_doc, model_used = await call_claude_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=settings.CLAUDE_SONNET_MODEL,
        temperature=0.2,
    )

    # ── 4. Validate response structure ───────────────────────────────────────
    required_keys = [
        "trajectory_indicator", "q1_plain_language", "q2_plain_language",
        "q3_plain_language", "q4_milestones", "q5_cause_plain",
        "predicted_questions", "key_numbers_panel"
    ]
    missing = [k for k in required_keys if k not in raw_doc]
    if missing:
        logger.error(f"Claude briefing response missing keys: {missing}")
        raise HTTPException(
            status_code=502,
            detail=f"AI response incomplete — missing: {', '.join(missing)}. Please retry."
        )

    # ── 5. Parse milestones ───────────────────────────────────────────────────
    from schemas import BriefingMilestone, PredictedQA
    milestones = [BriefingMilestone(**m) for m in raw_doc.get("q4_milestones", [])]
    predicted_qas = [PredictedQA(**q) for q in raw_doc.get("predicted_questions", [])]

    briefing_doc = BriefingDocument(
        trajectory_indicator=raw_doc["trajectory_indicator"],
        trajectory_label=raw_doc.get("trajectory_label", ""),
        q1_clinical_summary=raw_doc.get("q1_clinical_summary", {}),
        q1_plain_language=raw_doc["q1_plain_language"],
        q1_trajectory_statement=raw_doc.get("q1_trajectory_statement", ""),
        q1_do_not_say=raw_doc.get("q1_do_not_say", []),
        q2_treatment_items=raw_doc.get("q2_treatment_items", []),
        q2_specialists=raw_doc.get("q2_specialists", []),
        q2_plain_language=raw_doc["q2_plain_language"],
        q2_pending_reviews=raw_doc.get("q2_pending_reviews", []),
        q3_ventilator_assessment=raw_doc.get("q3_ventilator_assessment", {}),
        q3_plain_language=raw_doc["q3_plain_language"],
        q3_conditional_phrases=raw_doc.get("q3_conditional_phrases", {}),
        q4_milestones=milestones,
        q4_plain_language=raw_doc.get("q4_plain_language", ""),
        q5_cause_plain=raw_doc["q5_cause_plain"],
        q5_risk_factor_framings=raw_doc.get("q5_risk_factor_framings", []),
        q5_escalation_prompt=raw_doc.get("q5_escalation_prompt"),
        predicted_questions=predicted_qas,
        key_numbers_panel=raw_doc.get("key_numbers_panel", []),
    )

    # ── 6. Store briefing record ──────────────────────────────────────────────
    briefing = FamilyBriefing(
        patient_id=payload.patient_id,
        conducted_by_id=conducted_by_id,
        status=BriefingStatus.GENERATED,
        clinical_snapshot=payload.model_dump(),
        ai_briefing_doc=raw_doc,
        ai_model=model_used,
    )
    db.add(briefing)

    # Update patient last briefing and next due
    patient.last_briefing_at = datetime.now(timezone.utc)
    patient.next_briefing_due = _calculate_next_briefing(payload.trajectory)
    patient.trajectory = payload.trajectory

    await db.flush()

    return BriefingGenerateResponse(
        briefing_id=briefing.id,
        document=briefing_doc,
        generated_at=datetime.now(timezone.utc),
    )


async def complete_briefing(
    request: BriefingCompleteRequest,
    conducted_by_id: uuid.UUID,
    db: AsyncSession,
) -> BriefingOut:
    """Mark a briefing as completed and file the formal log."""
    result = await db.execute(
        select(FamilyBriefing).where(FamilyBriefing.id == request.briefing_id)
    )
    briefing = result.scalar_one_or_none()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    now = datetime.now(timezone.utc)
    briefing.conducted_by_id = conducted_by_id
    briefing.status = BriefingStatus.COMPLETED
    briefing.family_members = request.family_members
    briefing.topics_covered = request.topics_covered
    briefing.questions_raised = request.questions_raised
    briefing.family_understanding = request.family_understanding
    briefing.interpreter_used = request.interpreter_used
    briefing.interpreter_language = request.interpreter_language
    briefing.follow_up_promised = request.follow_up_promised
    briefing.duration_minutes = request.duration_minutes
    briefing.completed_at = now
    briefing.approved_at = now

    await db.flush()
    return BriefingOut.model_validate(briefing)
