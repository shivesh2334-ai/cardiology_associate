"""
AC Agent — Pydantic Schemas
Request / Response validation for all endpoints.
"""

import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, field_validator

from models import (
    UserRole, PatientStatus, ClinicalTrajectory, NoteType,
    NoteStatus, BriefingStatus, UrgencyLevel, VentilatorStatus
)


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    full_name: str
    role: str
    designation: str

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    designation: str
    registration_no: Optional[str] = None
    role: UserRole
    hospital_id: Optional[uuid.UUID] = None
    password: str

class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    designation: str
    registration_no: Optional[str]
    role: UserRole
    is_active: bool
    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
#  PATIENT
# ══════════════════════════════════════════════════════════════════════════════

class PatientCreate(BaseModel):
    uhid: str
    abha_id: Optional[str] = None
    full_name: str
    age: int
    sex: str
    contact_number: Optional[str] = None
    address: Optional[str] = None
    ward: Optional[str] = None
    bed_number: Optional[str] = None
    admitted_at: datetime
    primary_diagnosis: Optional[str] = None
    attending_consultant: Optional[str] = None
    ai_consent: bool = False
    ai_consent_by: Optional[str] = None

class PatientUpdate(BaseModel):
    ward: Optional[str] = None
    bed_number: Optional[str] = None
    primary_diagnosis: Optional[str] = None
    diagnosis_confirmed: Optional[bool] = None
    attending_consultant: Optional[str] = None
    trajectory: Optional[ClinicalTrajectory] = None
    status: Optional[PatientStatus] = None

class PatientOut(BaseModel):
    id: uuid.UUID
    uhid: str
    abha_id: Optional[str]
    full_name: str
    age: int
    sex: str
    ward: Optional[str]
    bed_number: Optional[str]
    admitted_at: datetime
    status: PatientStatus
    primary_diagnosis: Optional[str]
    diagnosis_confirmed: bool
    attending_consultant: Optional[str]
    trajectory: ClinicalTrajectory
    last_briefing_at: Optional[datetime]
    next_briefing_due: Optional[datetime]
    ai_consent: bool
    model_config = {"from_attributes": True}

class PatientListItem(BaseModel):
    """Compact view for the patient list screen."""
    id: uuid.UUID
    uhid: str
    full_name: str
    age: int
    sex: str
    ward: Optional[str]
    bed_number: Optional[str]
    primary_diagnosis: Optional[str]
    trajectory: ClinicalTrajectory
    admitted_at: datetime
    days_admitted: int
    briefing_overdue: bool
    has_pending_results: bool
    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
#  VITALS
# ══════════════════════════════════════════════════════════════════════════════

class VitalsCreate(BaseModel):
    recorded_at: datetime
    sbp: Optional[float] = None
    dbp: Optional[float] = None
    map: Optional[float] = None
    heart_rate: Optional[int] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    gcs: Optional[int] = None
    urine_output_ml: Optional[float] = None
    cvp: Optional[float] = None
    vasopressor_drug: Optional[str] = None
    vasopressor_dose: Optional[str] = None
    vasopressor_trend: Optional[str] = None

class VitalsOut(VitalsCreate):
    id: uuid.UUID
    patient_id: uuid.UUID
    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
#  ICU DATA
# ══════════════════════════════════════════════════════════════════════════════

class ICUDataUpsert(BaseModel):
    ventilator_status: VentilatorStatus = VentilatorStatus.NOT_VENTILATED
    ventilator_mode: Optional[str] = None
    fio2: Optional[float] = None
    peep: Optional[float] = None
    tidal_volume: Optional[float] = None
    rr_ventilator: Optional[int] = None
    plateau_pressure: Optional[float] = None
    weaning_readiness: Optional[str] = None
    estimated_extubation: Optional[str] = None
    apache_ii: Optional[int] = None
    sofa_score: Optional[int] = None

class ICUDataOut(ICUDataUpsert):
    id: uuid.UUID
    patient_id: uuid.UUID
    updated_at: datetime
    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
#  FAMILY BRIEFING
# ══════════════════════════════════════════════════════════════════════════════

class SpecialistInfo(BaseModel):
    name: str
    specialty: str
    last_review: Optional[str] = None   # human-readable e.g. "Today 11:30"
    notes: Optional[str] = None

class KeyLabValue(BaseModel):
    test_name: str
    value: str
    unit: Optional[str] = None
    previous_value: Optional[str] = None
    trend: Optional[str] = None         # improving / worsening / stable
    is_critical: bool = False

class BriefingInputPayload(BaseModel):
    """
    Everything the Associate confirms before the AI generates the briefing.
    This is the complete clinical snapshot.
    """
    patient_id: uuid.UUID

    # Current status
    trajectory: ClinicalTrajectory
    map_value: Optional[float] = None
    heart_rate: Optional[int] = None
    spo2: Optional[float] = None
    gcs: Optional[int] = None
    urine_output_4hr: Optional[str] = None     # e.g. "20 ml/hr"
    temperature: Optional[float] = None

    # Vasopressor
    vasopressor_drug: Optional[str] = None
    vasopressor_dose: Optional[str] = None
    vasopressor_trend: Optional[str] = None    # increasing / stable / weaning / off

    # Ventilator
    ventilator_status: VentilatorStatus = VentilatorStatus.NOT_VENTILATED
    ventilator_mode: Optional[str] = None
    fio2: Optional[float] = None
    peep: Optional[float] = None
    weaning_readiness: Optional[str] = None
    estimated_extubation: Optional[str] = None

    # Key investigations
    key_lab_values: list[KeyLabValue] = []
    imaging_summary: Optional[str] = None

    # Cause and treatment context
    procedure_done: Optional[str] = None        # e.g. "PTCA to LAD — stent placed"
    identified_risk_factors: list[str] = []
    diagnosis_plain: Optional[str] = None       # Override for plain-language diagnosis

    # Specialists involved
    specialists: list[SpecialistInfo] = []

    # Additional context for AI
    associate_notes: Optional[str] = None       # Free text the Associate wants to include

class BriefingMilestone(BaseModel):
    step: int
    description: str
    status: str   # achieved / in_progress / not_yet

class PredictedQA(BaseModel):
    question: str
    answer_framework: str
    answer_full: str

class BriefingDocument(BaseModel):
    """Complete AI-generated briefing document — returned to the app."""
    trajectory_indicator: str
    trajectory_label: str

    # Q1
    q1_clinical_summary: dict[str, Any]
    q1_plain_language: str
    q1_trajectory_statement: str
    q1_do_not_say: list[str]

    # Q2
    q2_treatment_items: list[dict[str, str]]
    q2_specialists: list[dict[str, str]]
    q2_plain_language: str
    q2_pending_reviews: list[str]

    # Q3
    q3_ventilator_assessment: dict[str, Any]
    q3_plain_language: str
    q3_conditional_phrases: dict[str, str]

    # Q4
    q4_milestones: list[BriefingMilestone]
    q4_plain_language: str

    # Q5
    q5_cause_plain: str
    q5_risk_factor_framings: list[dict[str, str]]
    q5_escalation_prompt: Optional[str]

    # Predicted follow-up
    predicted_questions: list[PredictedQA]

    # Co-pilot helpers
    key_numbers_panel: list[dict[str, str]]   # 3 most critical values

class BriefingGenerateResponse(BaseModel):
    briefing_id: uuid.UUID
    document: BriefingDocument
    generated_at: datetime

class BriefingCompleteRequest(BaseModel):
    briefing_id: uuid.UUID
    family_members: list[dict[str, str]]        # [{name, relationship}]
    topics_covered: list[str]                   # ["q1","q2","q3","q4","q5"]
    questions_raised: Optional[str] = None
    family_understanding: str                   # good / partial / poor
    interpreter_used: bool = False
    interpreter_language: Optional[str] = None
    follow_up_promised: Optional[str] = None
    duration_minutes: Optional[int] = None

class BriefingOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    status: BriefingStatus
    created_at: datetime
    completed_at: Optional[datetime]
    topics_covered: Optional[list]
    family_members: Optional[list]
    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
#  CLINICAL NOTES
# ══════════════════════════════════════════════════════════════════════════════

class NoteInputPayload(BaseModel):
    """Structured input for clinical note generation."""
    patient_id: uuid.UUID
    note_type: NoteType

    # Subjective
    patient_complaints: Optional[str] = None
    significant_events: Optional[str] = None   # What happened since last note

    # Objective
    vitals: Optional[VitalsCreate] = None
    examination_findings: Optional[str] = None
    new_lab_results: list[KeyLabValue] = []
    imaging_results: Optional[str] = None

    # Current medications (active list)
    medication_changes: Optional[str] = None    # New additions, changes, discontinuations

    # Assessment context
    diagnosis_status: Optional[str] = None      # working / confirmed + diagnosis
    clinical_interpretation: Optional[str] = None  # Associate's own clinical thinking

    # Plan inputs
    investigations_ordered: list[str] = []
    referrals_made: list[str] = []
    consultant_interactions: list[dict[str, str]] = []  # [{name, specialty, mode, recommendation}]
    procedures_done: Optional[str] = None
    nursing_instructions: Optional[str] = None
    next_review_plan: Optional[str] = None

    # ICU specific
    icu_data: Optional[ICUDataUpsert] = None

class SOAPNote(BaseModel):
    """Structured SOAP note from Claude."""
    note_type: str
    subjective: str
    objective_vitals: Optional[str] = None
    objective_investigations: Optional[str] = None
    objective_examination: Optional[str] = None
    assessment: str
    plan: str
    discussion: Optional[str] = None
    next_review_trigger: str
    quality_flags: list[str] = []

class NoteGenerateResponse(BaseModel):
    note_id: uuid.UUID
    soap_note: SOAPNote
    generated_at: datetime
    quality_flags: list[str]

class NoteApproveRequest(BaseModel):
    note_id: uuid.UUID
    # Associate may edit any SOAP section before approving
    subjective_override: Optional[str] = None
    objective_override: Optional[str] = None
    assessment_override: Optional[str] = None
    plan_override: Optional[str] = None
    discussion_override: Optional[str] = None

class NoteOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    note_type: NoteType
    status: NoteStatus
    subjective: Optional[str]
    objective: Optional[str]
    assessment: Optional[str]
    plan: Optional[str]
    discussion: Optional[str]
    ai_generated: bool
    approved_at: Optional[datetime]
    approved_by_name: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
#  SHARED
# ══════════════════════════════════════════════════════════════════════════════

class SuccessResponse(BaseModel):
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
