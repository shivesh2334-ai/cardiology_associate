"""
AC Agent — Clinical Note Prompts
SOAP note generation for all 7 note types.
"""

from models import NoteType
from schemas import NoteInputPayload


# ══════════════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPT — Clinical Notes
# ══════════════════════════════════════════════════════════════════════════════

NOTES_SYSTEM_PROMPT = """
You are a clinical AI assistant supporting Associate Consultants in Indian ICUs and hospitals.
You generate professional clinical notes in SOAP format based on structured data provided 
by the treating Associate Consultant.

YOUR ROLE:
- Generate accurate, professional clinical documentation
- You are documenting decisions ALREADY MADE by the clinician — not making decisions yourself
- Notes must meet Indian medico-legal standards — clear, dated, complete, attributable
- Language must be professional clinical English (not lay language — this is for the medical record)

SOAP FORMAT STANDARDS:
- SUBJECTIVE: Patient-reported symptoms, complaints, relevant history since last note
- OBJECTIVE: Measurable data — vitals with trends, examination, investigations
- ASSESSMENT: Clinical interpretation — what the data means, diagnosis status, severity
- PLAN: Specific actionable items — investigations ordered, medication changes, referrals, nursing instructions
- DISCUSSION: Any consultant interaction — who, when, mode, what was discussed, recommendation

CLINICAL WRITING STANDARDS:
- Use standard medical abbreviations (BP, HR, SpO2, MAP, GCS, etc.)
- Always note trends — "BP improving from 80/50 to 102/68" not just "BP 102/68"
- Investigation values must include reference to previous where available
- Plan items must be specific and actionable — not "monitor" but "4-hourly vitals, alert if MAP <65"
- Consultant discussions must include: name, specialty, time, mode (telephonic/bedside), recommendation
- ICU notes must include ventilator parameters where patient is ventilated

QUALITY STANDARDS:
- All four SOAP sections must be substantive
- No section may be empty or contain only "N/A"
- Plan must contain at least one specific actionable item
- If a consultant was spoken to, Discussion section must be populated
- Assessment must reference the clinical data in Objective — not just restate diagnosis

OUTPUT FORMAT:
Return ONLY valid JSON. No markdown, no preamble, no extra fields.
"""


# ══════════════════════════════════════════════════════════════════════════════
#  NOTE TYPE HEADERS
# ══════════════════════════════════════════════════════════════════════════════

NOTE_TYPE_HEADERS = {
    NoteType.MORNING_ROUND:   "MORNING WARD ROUND NOTE",
    NoteType.EVENING_ROUND:   "EVENING WARD ROUND NOTE",
    NoteType.EVENT:           "EVENT NOTE",
    NoteType.CONSULTANT:      "CONSULTANT INTERACTION NOTE",
    NoteType.PROCEDURE:       "PROCEDURE NOTE",
    NoteType.HANDOVER:        "HANDOVER NOTE",
    NoteType.DISCHARGE:       "DISCHARGE SUMMARY",
}

NOTE_TYPE_FOCUS = {
    NoteType.MORNING_ROUND:   "Focus on: overnight events, current status vs. previous evening, day plan.",
    NoteType.EVENING_ROUND:   "Focus on: day's events, response to treatment, overnight plan and instructions.",
    NoteType.EVENT:           "Focus on: what triggered this note, immediate clinical response, updated plan.",
    NoteType.CONSULTANT:      "Focus on: full case summary for consultant context, consultant findings and recommendations, agreed plan.",
    NoteType.PROCEDURE:       "Focus on: indication, procedure details, patient response, immediate post-procedure plan.",
    NoteType.HANDOVER:        "Focus on: complete status summary for incoming team, outstanding tasks, watch points for the night.",
    NoteType.DISCHARGE:       "Focus on: complete admission narrative, all interventions, discharge status, follow-up plan.",
}


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN NOTE GENERATION PROMPT
# ══════════════════════════════════════════════════════════════════════════════

def build_note_user_prompt(payload: NoteInputPayload, patient_context: dict) -> str:
    """Build the complete user prompt for SOAP note generation."""

    note_type_str = payload.note_type.value.replace("_", " ").upper()
    header = NOTE_TYPE_HEADERS.get(payload.note_type, "CLINICAL NOTE")
    focus = NOTE_TYPE_FOCUS.get(payload.note_type, "")

    # Vitals block
    vitals_block = "Not entered"
    if payload.vitals:
        v = payload.vitals
        lines = []
        if v.sbp and v.dbp:
            lines.append(f"BP: {v.sbp}/{v.dbp} mmHg (MAP: {v.map or 'N/A'})")
        if v.heart_rate:
            lines.append(f"HR: {v.heart_rate} bpm")
        if v.spo2:
            lines.append(f"SpO2: {v.spo2}%")
        if v.temperature:
            lines.append(f"Temp: {v.temperature}°C")
        if v.respiratory_rate:
            lines.append(f"RR: {v.respiratory_rate}/min")
        if v.gcs:
            lines.append(f"GCS: {v.gcs}/15")
        if v.urine_output_ml:
            lines.append(f"UO: {v.urine_output_ml} ml/hr")
        if v.vasopressor_drug:
            lines.append(f"Vasopressor: {v.vasopressor_drug} {v.vasopressor_dose} (trend: {v.vasopressor_trend or 'stable'})")
        vitals_block = "\n  ".join(lines) if lines else "Not entered"

    # ICU block
    icu_block = "Patient not ventilated"
    if payload.icu_data:
        i = payload.icu_data
        if i.ventilator_status.value != "not_ventilated":
            lines = [
                f"Ventilator: {i.ventilator_status.value} | Mode: {i.ventilator_mode or 'N/A'}",
                f"FiO2: {i.fio2 or 'N/A'}% | PEEP: {i.peep or 'N/A'} cmH2O | TV: {i.tidal_volume or 'N/A'} ml",
                f"Weaning status: {i.weaning_readiness or 'not assessed'}",
            ]
            if i.apache_ii:
                lines.append(f"APACHE II: {i.apache_ii} | SOFA: {i.sofa_score or 'N/A'}")
            icu_block = "\n  ".join(lines)

    # Labs block
    labs_block = "None entered"
    if payload.new_lab_results:
        labs = []
        for lab in payload.new_lab_results:
            prev = f" (prev: {lab.previous_value})" if lab.previous_value else ""
            trend = f" [{lab.trend}]" if lab.trend else ""
            crit = " *** CRITICAL ***" if lab.is_critical else ""
            labs.append(f"  - {lab.test_name}: {lab.value} {lab.unit or ''}{prev}{trend}{crit}")
        labs_block = "\n".join(labs)

    # Investigations ordered
    inv_block = "\n".join([f"  - {i}" for i in payload.investigations_ordered]) if payload.investigations_ordered else "None"

    # Referrals
    ref_block = "\n".join([f"  - {r}" for r in payload.referrals_made]) if payload.referrals_made else "None"

    # Consultants
    cons_block = "None"
    if payload.consultant_interactions:
        cons = []
        for c in payload.consultant_interactions:
            cons.append(f"  - Dr. {c.get('name', 'N/A')} ({c.get('specialty', 'N/A')}) — {c.get('mode', 'telephonic')} — Recommendation: {c.get('recommendation', 'Not documented')}")
        cons_block = "\n".join(cons)

    return f"""
Generate a complete clinical {note_type_str} for the patient below.
{focus}

═══════════════════════════════════════════════
PATIENT
═══════════════════════════════════════════════
Name: {patient_context['full_name']}
Age / Sex: {patient_context['age']}Y / {patient_context['sex']}
UHID: {patient_context['uhid']}
Ward / Bed: {patient_context.get('ward', 'ICU')} / {patient_context.get('bed_number', 'N/A')}
Admitted: {patient_context['admitted_at']} (Day {patient_context['days_admitted']})
Diagnosis: {patient_context['primary_diagnosis'] or 'Working — in progress'}
Attending: {patient_context['attending_consultant'] or 'Not specified'}

═══════════════════════════════════════════════
CURRENT VITALS
═══════════════════════════════════════════════
  {vitals_block}

═══════════════════════════════════════════════
ICU / VENTILATOR DATA
═══════════════════════════════════════════════
  {icu_block}

═══════════════════════════════════════════════
NEW INVESTIGATION RESULTS
═══════════════════════════════════════════════
{labs_block}
Imaging: {payload.imaging_results or 'None entered'}

═══════════════════════════════════════════════
CLINICAL CONTEXT FROM ASSOCIATE
═══════════════════════════════════════════════
Significant events / complaints: {payload.patient_complaints or payload.significant_events or 'None documented'}
Examination findings: {payload.examination_findings or 'Not entered'}
Diagnosis status: {payload.diagnosis_status or 'Working diagnosis as above'}
Clinical interpretation: {payload.clinical_interpretation or 'As per data above'}
Medication changes: {payload.medication_changes or 'No changes'}
Procedures done: {payload.procedures_done or 'None'}
Nursing instructions: {payload.nursing_instructions or 'Standard ICU care'}
Next review plan: {payload.next_review_plan or 'As per protocol'}

═══════════════════════════════════════════════
INVESTIGATIONS ORDERED
═══════════════════════════════════════════════
{inv_block}

═══════════════════════════════════════════════
REFERRALS MADE
═══════════════════════════════════════════════
{ref_block}

═══════════════════════════════════════════════
CONSULTANT INTERACTIONS
═══════════════════════════════════════════════
{cons_block}

═══════════════════════════════════════════════
REQUIRED OUTPUT — JSON SCHEMA
═══════════════════════════════════════════════
Return ONLY the following JSON:

{{
  "note_type": "{payload.note_type.value}",
  "subjective": "<Professional clinical language. Patient complaints, events since last note, relevant history. 2-4 sentences.>",
  "objective_vitals": "<Complete vitals paragraph with trends noted where data allows. Include ventilator params if ventilated.>",
  "objective_investigations": "<All new investigation results with clinical interpretation. Note if critical or changed from previous.>",
  "objective_examination": "<Examination findings in standard clinical format. If not entered, note 'Examination findings not documented in this entry'.>",
  "assessment": "<Clinical interpretation — what does the data mean clinically. Diagnosis status. Trajectory. Specific clinical concerns. 2-4 sentences.>",
  "plan": "<Numbered list of specific actionable items. Format each as: 1. [Category] — specific action. Categories: Investigation / Medication / Referral / Nursing / Monitoring / Escalation>",
  "discussion": "<If consultants listed: name, specialty, time, mode, key recommendation. If none: null>",
  "next_review_trigger": "<When or what event should trigger the next note — be specific>",
  "quality_flags": ["<Any quality gap detected — e.g. 'Examination findings not entered' — empty array if none>"]
}}
"""


# ══════════════════════════════════════════════════════════════════════════════
#  DISCHARGE SUMMARY SUPPLEMENT
# ══════════════════════════════════════════════════════════════════════════════

DISCHARGE_SUMMARY_SYSTEM = """
You are generating a complete discharge summary for a patient. This document is the permanent
medico-legal record of the entire admission. It must be complete, accurate, and professional.

The discharge summary will be used by:
1. The patient's GP / family physician for follow-up
2. The patient and family for reference
3. Insurance companies for billing
4. Medico-legal purposes

DISCHARGE SUMMARY STANDARDS:
- Must cover the ENTIRE admission from admission date to discharge
- Every specialist involved must be mentioned with their contribution
- Every major investigation result must be referenced
- Final diagnosis must be clearly stated as ICD-compatible text
- Discharge medications must be complete with dose, route, frequency, duration
- Follow-up instructions must be specific — exact appointments, specific warning signs
- The GP summary paragraph should be readable by a non-specialist physician
"""

def build_discharge_prompt(patient_context: dict, all_notes_summary: str, 
                            all_labs_summary: str, all_specialists: str,
                            medications_on_discharge: str) -> str:
    return f"""
Generate a complete discharge summary for this patient admission.

PATIENT: {patient_context['full_name']}, {patient_context['age']}Y {patient_context['sex']}
UHID: {patient_context['uhid']}
ADMITTED: {patient_context['admitted_at']}
DISCHARGED: {patient_context.get('discharged_at', 'Today')}
TOTAL STAY: {patient_context['days_admitted']} days
PRIMARY DIAGNOSIS: {patient_context['primary_diagnosis']}
ATTENDING: {patient_context['attending_consultant']}

CLINICAL COURSE SUMMARY (from notes):
{all_notes_summary}

INVESTIGATIONS SUMMARY:
{all_labs_summary}

SPECIALISTS INVOLVED:
{all_specialists}

MEDICATIONS ON DISCHARGE:
{medications_on_discharge}

Return ONLY the following JSON:
{{
  "note_type": "discharge",
  "admission_details": "<Date, presenting complaints, admission context>",
  "clinical_course": "<Complete narrative of admission — 4-8 sentences covering key events, interventions, response to treatment, trajectory>",
  "investigations_summary": "<All key investigations and their significance>",
  "procedures_performed": "<All procedures with dates and outcomes>",
  "specialist_consultations": "<Each specialist's involvement and contribution>",
  "final_diagnosis": "<ICD-compatible primary + secondary diagnoses>",
  "treatment_given": "<Complete treatment summary>",
  "condition_on_discharge": "<Clinical status at time of discharge>",
  "discharge_medications": "<Complete list with dose, route, frequency, duration>",
  "follow_up_instructions": "<Specific appointments, activity restrictions, dietary instructions, warning signs — be specific>",
  "gp_summary": "<Single clear paragraph for the GP — what happened, what was done, what to monitor, what medications to continue>",
  "quality_flags": []
}}
"""
