"""
AC Agent — Database Models
Full ORM for all MVP entities.
"""

import uuid
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, Boolean, DateTime, Float, Integer,
    ForeignKey, Enum as SAEnum, JSON, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ASSOCIATE   = "associate"
    CONSULTANT  = "consultant"
    ADMIN       = "admin"

class PatientStatus(str, enum.Enum):
    ACTIVE    = "active"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"
    DECEASED  = "deceased"

class ClinicalTrajectory(str, enum.Enum):
    IMPROVING    = "improving"
    STABLE       = "stable"
    GUARDED      = "guarded"
    CRITICAL     = "critical"
    DETERIORATING = "deteriorating"

class NoteType(str, enum.Enum):
    MORNING_ROUND   = "morning_round"
    EVENING_ROUND   = "evening_round"
    EVENT           = "event"
    CONSULTANT      = "consultant"
    PROCEDURE       = "procedure"
    HANDOVER        = "handover"
    DISCHARGE       = "discharge"

class NoteStatus(str, enum.Enum):
    DRAFT    = "draft"
    APPROVED = "approved"
    ADDENDED = "addended"

class BriefingStatus(str, enum.Enum):
    GENERATED  = "generated"
    IN_PROGRESS = "in_progress"
    COMPLETED  = "completed"

class UrgencyLevel(str, enum.Enum):
    ROUTINE   = "routine"
    URGENT    = "urgent"
    EMERGENCY = "emergency"

class VentilatorStatus(str, enum.Enum):
    NOT_VENTILATED    = "not_ventilated"
    VENTILATED        = "ventilated"
    WEANING           = "weaning"
    WEANING_TRIAL     = "weaning_trial"
    EXTUBATED         = "extubated"


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id:            Mapped[uuid.UUID]         = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email:         Mapped[str]               = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name:     Mapped[str]               = mapped_column(String(255), nullable=False)
    designation:   Mapped[str]               = mapped_column(String(100), nullable=False)
    registration_no: Mapped[Optional[str]]   = mapped_column(String(50))
    role:          Mapped[UserRole]          = mapped_column(SAEnum(UserRole), nullable=False)
    hospital_id:   Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"))
    hashed_password: Mapped[str]             = mapped_column(String(255), nullable=False)
    is_active:     Mapped[bool]              = mapped_column(Boolean, default=True)
    created_at:    Mapped[datetime]          = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login:    Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    hospital:      Mapped[Optional["Hospital"]] = relationship("Hospital", back_populates="users")
    notes:         Mapped[list["ClinicalNote"]] = relationship("ClinicalNote", back_populates="author")
    briefings:     Mapped[list["FamilyBriefing"]] = relationship("FamilyBriefing", back_populates="conducted_by")


# ── Hospital ──────────────────────────────────────────────────────────────────

class Hospital(Base):
    __tablename__ = "hospitals"

    id:            Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name:          Mapped[str]       = mapped_column(String(255), nullable=False)
    tier:          Mapped[str]       = mapped_column(String(50))   # corporate / mid-size / primary
    city:          Mapped[str]       = mapped_column(String(100))
    state:         Mapped[str]       = mapped_column(String(100))
    is_active:     Mapped[bool]      = mapped_column(Boolean, default=True)
    created_at:    Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    users:    Mapped[list["User"]]    = relationship("User", back_populates="hospital")
    patients: Mapped[list["Patient"]] = relationship("Patient", back_populates="hospital")


# ── Patient ───────────────────────────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"

    id:              Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id:     Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    abha_id:         Mapped[Optional[str]]   = mapped_column(String(50), index=True)    # Phase 2
    uhid:            Mapped[str]             = mapped_column(String(50), nullable=False, index=True)

    # Demographics
    full_name:       Mapped[str]             = mapped_column(String(255), nullable=False)
    age:             Mapped[int]             = mapped_column(Integer, nullable=False)
    sex:             Mapped[str]             = mapped_column(String(10), nullable=False)
    contact_number:  Mapped[Optional[str]]   = mapped_column(String(20))
    address:         Mapped[Optional[str]]   = mapped_column(Text)

    # Admission
    ward:            Mapped[Optional[str]]   = mapped_column(String(50))
    bed_number:      Mapped[Optional[str]]   = mapped_column(String(20))
    admitted_at:     Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False)
    discharged_at:   Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status:          Mapped[PatientStatus]   = mapped_column(SAEnum(PatientStatus), default=PatientStatus.ACTIVE)

    # Clinical
    primary_diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    diagnosis_confirmed: Mapped[bool]        = mapped_column(Boolean, default=False)
    attending_consultant: Mapped[Optional[str]] = mapped_column(String(255))
    trajectory:       Mapped[ClinicalTrajectory] = mapped_column(SAEnum(ClinicalTrajectory), default=ClinicalTrajectory.STABLE)
    last_briefing_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_briefing_due: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # AI assistance consent
    ai_consent:      Mapped[bool]            = mapped_column(Boolean, default=False)
    ai_consent_by:   Mapped[Optional[str]]   = mapped_column(String(255))
    ai_consent_at:   Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at:      Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    hospital:        Mapped["Hospital"]      = relationship("Hospital", back_populates="patients")
    vitals:          Mapped[list["VitalSigns"]]     = relationship("VitalSigns", back_populates="patient", order_by="VitalSigns.recorded_at.desc()")
    labs:            Mapped[list["LabResult"]]       = relationship("LabResult", back_populates="patient")
    medications:     Mapped[list["Medication"]]      = relationship("Medication", back_populates="patient")
    notes:           Mapped[list["ClinicalNote"]]    = relationship("ClinicalNote", back_populates="patient", order_by="ClinicalNote.created_at.desc()")
    briefings:       Mapped[list["FamilyBriefing"]]  = relationship("FamilyBriefing", back_populates="patient", order_by="FamilyBriefing.created_at.desc()")
    referrals:       Mapped[list["Referral"]]        = relationship("Referral", back_populates="patient")
    icu_data:        Mapped[Optional["ICUData"]]     = relationship("ICUData", back_populates="patient", uselist=False)


# ── Vital Signs ───────────────────────────────────────────────────────────────

class VitalSigns(Base):
    __tablename__ = "vital_signs"

    id:             Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id:     Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    recorded_at:    Mapped[datetime]       = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_by:    Mapped[Optional[str]]  = mapped_column(String(255))

    # Core vitals
    sbp:            Mapped[Optional[float]] = mapped_column(Float)  # Systolic BP mmHg
    dbp:            Mapped[Optional[float]] = mapped_column(Float)  # Diastolic BP mmHg
    map:            Mapped[Optional[float]] = mapped_column(Float)  # Mean Arterial Pressure
    heart_rate:     Mapped[Optional[int]]   = mapped_column(Integer)
    spo2:           Mapped[Optional[float]] = mapped_column(Float)  # %
    temperature:    Mapped[Optional[float]] = mapped_column(Float)  # Celsius
    respiratory_rate: Mapped[Optional[int]] = mapped_column(Integer)
    gcs:            Mapped[Optional[int]]   = mapped_column(Integer)  # 3-15

    # ICU specific
    urine_output_ml: Mapped[Optional[float]] = mapped_column(Float)  # ml/hr
    cvp:            Mapped[Optional[float]]  = mapped_column(Float)   # cmH2O

    # Vasopressors
    vasopressor_drug:  Mapped[Optional[str]]   = mapped_column(String(100))
    vasopressor_dose:  Mapped[Optional[str]]   = mapped_column(String(50))   # mcg/kg/min
    vasopressor_trend: Mapped[Optional[str]]   = mapped_column(String(20))   # increasing/stable/weaning/off

    patient: Mapped["Patient"] = relationship("Patient", back_populates="vitals")


# ── ICU Data ──────────────────────────────────────────────────────────────────

class ICUData(Base):
    __tablename__ = "icu_data"

    id:              Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id:      Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, unique=True)

    # Ventilator
    ventilator_status: Mapped[VentilatorStatus] = mapped_column(SAEnum(VentilatorStatus), default=VentilatorStatus.NOT_VENTILATED)
    ventilator_mode:   Mapped[Optional[str]]    = mapped_column(String(50))   # AC/VC, SIMV, PSV
    fio2:              Mapped[Optional[float]]  = mapped_column(Float)        # %
    peep:              Mapped[Optional[float]]  = mapped_column(Float)        # cmH2O
    tidal_volume:      Mapped[Optional[float]]  = mapped_column(Float)        # ml
    rr_ventilator:     Mapped[Optional[int]]    = mapped_column(Integer)
    plateau_pressure:  Mapped[Optional[float]]  = mapped_column(Float)
    weaning_readiness: Mapped[Optional[str]]    = mapped_column(String(50))   # not_ready / approaching / trial_ready
    estimated_extubation: Mapped[Optional[str]] = mapped_column(String(100))  # free text estimate

    # Monitoring
    apache_ii:         Mapped[Optional[int]]    = mapped_column(Integer)
    sofa_score:        Mapped[Optional[int]]    = mapped_column(Integer)

    updated_at:        Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient: Mapped["Patient"] = relationship("Patient", back_populates="icu_data")


# ── Lab Results ───────────────────────────────────────────────────────────────

class LabResult(Base):
    __tablename__ = "lab_results"

    id:              Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id:      Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    test_name:       Mapped[str]           = mapped_column(String(100), nullable=False)
    value:           Mapped[str]           = mapped_column(String(100), nullable=False)
    unit:            Mapped[Optional[str]] = mapped_column(String(50))
    reference_range: Mapped[Optional[str]] = mapped_column(String(100))
    is_critical:     Mapped[bool]          = mapped_column(Boolean, default=False)
    is_reviewed:     Mapped[bool]          = mapped_column(Boolean, default=False)
    collected_at:    Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False)
    reported_at:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    previous_value:  Mapped[Optional[str]] = mapped_column(String(100))
    trend:           Mapped[Optional[str]] = mapped_column(String(20))  # improving/worsening/stable

    patient: Mapped["Patient"] = relationship("Patient", back_populates="labs")


# ── Medications ───────────────────────────────────────────────────────────────

class Medication(Base):
    __tablename__ = "medications"

    id:              Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id:      Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    drug_name:       Mapped[str]           = mapped_column(String(200), nullable=False)
    dose:            Mapped[str]           = mapped_column(String(100), nullable=False)
    route:           Mapped[str]           = mapped_column(String(50), nullable=False)
    frequency:       Mapped[str]           = mapped_column(String(100), nullable=False)
    indication:      Mapped[Optional[str]] = mapped_column(String(255))
    started_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False)
    stopped_at:      Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active:       Mapped[bool]          = mapped_column(Boolean, default=True)
    prescribed_by:   Mapped[Optional[str]] = mapped_column(String(255))

    patient: Mapped["Patient"] = relationship("Patient", back_populates="medications")


# ── Referrals ─────────────────────────────────────────────────────────────────

class Referral(Base):
    __tablename__ = "referrals"

    id:              Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id:      Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    specialty:       Mapped[str]           = mapped_column(String(100), nullable=False)
    consultant_name: Mapped[Optional[str]] = mapped_column(String(255))
    urgency:         Mapped[UrgencyLevel]  = mapped_column(SAEnum(UrgencyLevel), nullable=False)
    clinical_question: Mapped[str]         = mapped_column(Text, nullable=False)
    referred_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reviewed_at:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    consultant_notes: Mapped[Optional[str]] = mapped_column(Text)
    is_completed:    Mapped[bool]          = mapped_column(Boolean, default=False)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="referrals")


# ── Clinical Notes ────────────────────────────────────────────────────────────

class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    id:              Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id:      Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    author_id:       Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    note_type:       Mapped[NoteType]      = mapped_column(SAEnum(NoteType), nullable=False)
    status:          Mapped[NoteStatus]    = mapped_column(SAEnum(NoteStatus), default=NoteStatus.DRAFT)

    # SOAP sections — stored as text and raw AI JSON
    subjective:      Mapped[Optional[str]] = mapped_column(Text)
    objective:       Mapped[Optional[str]] = mapped_column(Text)
    assessment:      Mapped[Optional[str]] = mapped_column(Text)
    plan:            Mapped[Optional[str]] = mapped_column(Text)
    discussion:      Mapped[Optional[str]] = mapped_column(Text)

    # AI metadata
    ai_generated:    Mapped[bool]          = mapped_column(Boolean, default=True)
    ai_model:        Mapped[Optional[str]] = mapped_column(String(100))
    ai_raw_output:   Mapped[Optional[dict]] = mapped_column(JSON)   # full Claude response
    author_edits:    Mapped[Optional[dict]] = mapped_column(JSON)   # what the Associate changed

    # Approval
    approved_at:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by_name: Mapped[Optional[str]]     = mapped_column(String(255))
    approved_by_reg:  Mapped[Optional[str]]     = mapped_column(String(50))

    created_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Addendum chain
    parent_note_id:  Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("clinical_notes.id"))

    patient: Mapped["Patient"]     = relationship("Patient", back_populates="notes")
    author:  Mapped["User"]        = relationship("User", back_populates="notes")
    addenda: Mapped[list["ClinicalNote"]] = relationship("ClinicalNote")


# ── Family Briefings ──────────────────────────────────────────────────────────

class FamilyBriefing(Base):
    __tablename__ = "family_briefings"

    id:              Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id:      Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    conducted_by_id: Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status:          Mapped[BriefingStatus] = mapped_column(SAEnum(BriefingStatus), default=BriefingStatus.GENERATED)

    # Family members present
    family_members:  Mapped[Optional[list]] = mapped_column(JSON)  # [{name, relationship}]

    # Input snapshot
    clinical_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)  # vitals + labs at time of briefing

    # AI-generated content
    ai_briefing_doc:   Mapped[Optional[dict]] = mapped_column(JSON)  # full structured briefing from Claude
    ai_model:          Mapped[Optional[str]]  = mapped_column(String(100))

    # Topics covered (from co-pilot checklist)
    topics_covered:    Mapped[Optional[list]] = mapped_column(JSON)  # ["q1","q2","q3","q4","q5"]
    questions_raised:  Mapped[Optional[str]]  = mapped_column(Text)  # Additional questions from family

    # Post-briefing
    family_understanding: Mapped[Optional[str]] = mapped_column(String(50))  # good/partial/poor
    interpreter_used:     Mapped[bool]           = mapped_column(Boolean, default=False)
    interpreter_language: Mapped[Optional[str]]  = mapped_column(String(50))
    follow_up_promised:   Mapped[Optional[str]]  = mapped_column(Text)
    next_briefing_due:    Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Timing
    started_at:        Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at:      Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_minutes:  Mapped[Optional[int]]      = mapped_column(Integer)
    created_at:        Mapped[datetime]            = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Approval
    approved_at:       Mapped[Optional[datetime]]  = mapped_column(DateTime(timezone=True))

    patient:      Mapped["Patient"] = relationship("Patient", back_populates="briefings")
    conducted_by: Mapped["User"]    = relationship("User", back_populates="briefings")
