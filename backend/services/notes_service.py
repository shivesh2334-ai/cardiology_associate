"""
AC Agent — Clinical Notes Service
SOAP note generation, approval, and discharge summary.
"""

import uuid
import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Patient, ClinicalNote, NoteStatus, NoteType, VitalSigns, ICUData
from schemas import (
    NoteInputPayload, NoteGenerateResponse, SOAPNote,
    NoteApproveRequest, NoteOut,
)
from services.claude_service import call_claude_json
from prompts.clinical_notes import (
    NOTES_SYSTEM_PROMPT,
    DISCHARGE_SUMMARY_SYSTEM,
    build_note_user_prompt,
    build_discharge_prompt,
)

logger = logging.getLogger(__name__)

# Quality check — required keys in note output
REQUIRED_NOTE_KEYS = ["subjective", "objective_vitals", "assessment", "plan", "next_review_trigger"]


def _patient_to_context(patient: Patient) -> dict:
    from datetime import timezone as tz
    now = datetime.now(tz.utc)
    admitted = patient.admitted_at
    if admitted.tzinfo is None:
        admitted = admitted.replace(tzinfo=tz.utc)
    days = max(1, (now - admitted).days)
    return {
        "full_name": patient.full_name,
        "age": patient.age,
        "sex": patient.sex,
        "uhid": patient.uhid,
        "admitted_at": admitted.strftime("%d %b %Y"),
        "days_admitted": days,
        "ward": patient.ward,
        "bed_number": patient.bed_number,
        "primary_diagnosis": patient.primary_diagnosis,
        "attending_consultant": patient.attending_consultant,
    }


def _validate_note_quality(raw: dict) -> list[str]:
    """Return list of quality flags — empty means passed."""
    flags = []
    for key in REQUIRED_NOTE_KEYS:
        val = raw.get(key, "")
        if not val or str(val).strip().lower() in ("n/a", "not entered", "none", ""):
            flags.append(f"Section '{key}' is empty or insufficient")
    if "plan" in raw:
        plan = raw["plan"]
        if plan and len(str(plan).strip()) < 20:
            flags.append("Plan section is too brief — add specific actions")
    return flags


async def generate_note(
    payload: NoteInputPayload,
    author_id: uuid.UUID,
    db: AsyncSession,
) -> NoteGenerateResponse:
    """Generate a SOAP note using Claude."""

    # Load patient
    result = await db.execute(select(Patient).where(Patient.id == payload.patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if not patient.ai_consent:
        raise HTTPException(status_code=403, detail="AI consent not obtained for this patient")

    patient_context = _patient_to_context(patient)

    # Build and send prompt
    user_prompt = build_note_user_prompt(payload, patient_context)

    raw_note, model_used = await call_claude_json(
        system_prompt=NOTES_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=settings.CLAUDE_SONNET_MODEL,
        temperature=0.15,   # Very consistent for clinical notes
    )

    # Quality validation
    quality_flags = _validate_note_quality(raw_note)
    if quality_flags:
        logger.warning(f"Note quality flags for patient {payload.patient_id}: {quality_flags}")

    # Parse SOAP note
    soap = SOAPNote(
        note_type=raw_note.get("note_type", payload.note_type.value),
        subjective=raw_note.get("subjective", ""),
        objective_vitals=raw_note.get("objective_vitals"),
        objective_investigations=raw_note.get("objective_investigations"),
        objective_examination=raw_note.get("objective_examination"),
        assessment=raw_note.get("assessment", ""),
        plan=raw_note.get("plan", ""),
        discussion=raw_note.get("discussion"),
        next_review_trigger=raw_note.get("next_review_trigger", "As clinically indicated"),
        quality_flags=raw_note.get("quality_flags", []),
    )

    # Compose objective section
    objective_parts = []
    if soap.objective_vitals:
        objective_parts.append(soap.objective_vitals)
    if soap.objective_investigations:
        objective_parts.append(soap.objective_investigations)
    if soap.objective_examination:
        objective_parts.append(soap.objective_examination)
    objective_full = "\n\n".join(objective_parts)

    # Store as draft
    note = ClinicalNote(
        patient_id=payload.patient_id,
        author_id=author_id,
        note_type=payload.note_type,
        status=NoteStatus.DRAFT,
        subjective=soap.subjective,
        objective=objective_full,
        assessment=soap.assessment,
        plan=soap.plan,
        discussion=soap.discussion,
        ai_generated=True,
        ai_model=model_used,
        ai_raw_output=raw_note,
    )
    db.add(note)

    # Update vitals if provided
    if payload.vitals:
        v = payload.vitals
        vitals_row = VitalSigns(
            patient_id=payload.patient_id,
            recorded_at=v.recorded_at,
            sbp=v.sbp, dbp=v.dbp, map=v.map,
            heart_rate=v.heart_rate, spo2=v.spo2,
            temperature=v.temperature, respiratory_rate=v.respiratory_rate,
            gcs=v.gcs, urine_output_ml=v.urine_output_ml,
            vasopressor_drug=v.vasopressor_drug,
            vasopressor_dose=v.vasopressor_dose,
            vasopressor_trend=v.vasopressor_trend,
        )
        db.add(vitals_row)

    await db.flush()

    return NoteGenerateResponse(
        note_id=note.id,
        soap_note=soap,
        generated_at=datetime.now(timezone.utc),
        quality_flags=quality_flags,
    )


async def approve_note(
    request: NoteApproveRequest,
    approver: "User",  # noqa
    db: AsyncSession,
) -> NoteOut:
    """Apply any Associate edits and approve the note."""
    result = await db.execute(select(ClinicalNote).where(ClinicalNote.id == request.note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.status == NoteStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Note is already approved")

    # Track what the Associate changed
    edits = {}
    if request.subjective_override is not None:
        edits["subjective"] = {"from": note.subjective, "to": request.subjective_override}
        note.subjective = request.subjective_override
    if request.objective_override is not None:
        edits["objective"] = {"from": note.objective, "to": request.objective_override}
        note.objective = request.objective_override
    if request.assessment_override is not None:
        edits["assessment"] = {"from": note.assessment, "to": request.assessment_override}
        note.assessment = request.assessment_override
    if request.plan_override is not None:
        edits["plan"] = {"from": note.plan, "to": request.plan_override}
        note.plan = request.plan_override
    if request.discussion_override is not None:
        edits["discussion"] = {"from": note.discussion, "to": request.discussion_override}
        note.discussion = request.discussion_override

    now = datetime.now(timezone.utc)
    note.status = NoteStatus.APPROVED
    note.approved_at = now
    note.approved_by_name = approver.full_name
    note.approved_by_reg = approver.registration_no
    note.author_edits = edits if edits else None

    await db.flush()
    return NoteOut.model_validate(note)


async def generate_discharge_summary(
    patient_id: uuid.UUID,
    author_id: uuid.UUID,
    discharge_data: dict,
    db: AsyncSession,
) -> NoteGenerateResponse:
    """Generate discharge summary from all admission notes."""

    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient_context = _patient_to_context(patient)

    # Fetch all approved notes
    notes_result = await db.execute(
        select(ClinicalNote).where(
            and_(
                ClinicalNote.patient_id == patient_id,
                ClinicalNote.status == NoteStatus.APPROVED,
                ClinicalNote.note_type != NoteType.DISCHARGE,
            )
        ).order_by(ClinicalNote.created_at)
    )
    all_notes = notes_result.scalars().all()

    # Summarise notes for prompt
    notes_summary_parts = []
    for n in all_notes:
        note_date = n.created_at.strftime("%d %b %Y %H:%M")
        notes_summary_parts.append(
            f"[{note_date} — {n.note_type.value}]\n"
            f"Assessment: {n.assessment or 'N/A'}\n"
            f"Plan: {n.plan or 'N/A'}"
        )
    notes_summary = "\n\n".join(notes_summary_parts) if notes_summary_parts else "No prior approved notes"

    # Build discharge prompt
    user_prompt = build_discharge_prompt(
        patient_context=patient_context,
        all_notes_summary=notes_summary,
        all_labs_summary=discharge_data.get("labs_summary", "Not provided"),
        all_specialists=discharge_data.get("specialists_summary", "Not provided"),
        medications_on_discharge=discharge_data.get("medications_on_discharge", "Not provided"),
    )

    raw_note, model_used = await call_claude_json(
        system_prompt=NOTES_SYSTEM_PROMPT + "\n\n" + DISCHARGE_SUMMARY_SYSTEM,
        user_prompt=user_prompt,
        max_tokens=4096,
        temperature=0.15,
    )

    # Build full note text from discharge fields
    full_text = (
        f"ADMISSION: {raw_note.get('admission_details', '')}\n\n"
        f"CLINICAL COURSE: {raw_note.get('clinical_course', '')}\n\n"
        f"INVESTIGATIONS: {raw_note.get('investigations_summary', '')}\n\n"
        f"PROCEDURES: {raw_note.get('procedures_performed', '')}\n\n"
        f"SPECIALIST CONSULTATIONS: {raw_note.get('specialist_consultations', '')}"
    )

    soap = SOAPNote(
        note_type=NoteType.DISCHARGE.value,
        subjective=raw_note.get("admission_details", ""),
        objective_vitals=raw_note.get("investigations_summary"),
        objective_investigations=None,
        objective_examination=None,
        assessment=f"FINAL DIAGNOSIS: {raw_note.get('final_diagnosis', '')}\n\n"
                   f"TREATMENT GIVEN: {raw_note.get('treatment_given', '')}",
        plan=f"DISCHARGE MEDICATIONS:\n{raw_note.get('discharge_medications', '')}\n\n"
             f"FOLLOW-UP INSTRUCTIONS:\n{raw_note.get('follow_up_instructions', '')}",
        discussion=raw_note.get("gp_summary"),
        next_review_trigger="As per follow-up plan",
        quality_flags=raw_note.get("quality_flags", []),
    )

    note = ClinicalNote(
        patient_id=patient_id,
        author_id=author_id,
        note_type=NoteType.DISCHARGE,
        status=NoteStatus.DRAFT,
        subjective=soap.subjective,
        objective=full_text,
        assessment=soap.assessment,
        plan=soap.plan,
        discussion=soap.discussion,
        ai_generated=True,
        ai_model=model_used,
        ai_raw_output=raw_note,
    )
    db.add(note)
    await db.flush()

    return NoteGenerateResponse(
        note_id=note.id,
        soap_note=soap,
        generated_at=datetime.now(timezone.utc),
        quality_flags=raw_note.get("quality_flags", []),
    )
