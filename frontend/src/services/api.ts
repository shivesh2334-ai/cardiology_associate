/**
 * AC Agent — API Service
 * All HTTP calls to the FastAPI backend.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

// ── HTTP client ────────────────────────────────────────────────────────────────

async function getToken(): Promise<string | null> {
  return AsyncStorage.getItem('access_token');
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  requiresAuth = true,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (requiresAuth) {
    const token = await getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const err = await response.json();
      detail = err.detail ?? err.error ?? detail;
    } catch {}
    throw new APIError(detail, response.status);
  }

  return response.json() as Promise<T>;
}

export class APIError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = 'APIError';
  }
}

const api = {
  get:    <T>(path: string) => request<T>('GET', path),
  post:   <T>(path: string, body: unknown) => request<T>('POST', path, body),
  patch:  <T>(path: string, body: unknown) => request<T>('PATCH', path, body),
  put:    <T>(path: string, body: unknown) => request<T>('PUT', path, body),
  delete: <T>(path: string) => request<T>('DELETE', path),
};


// ══════════════════════════════════════════════════════════════════════════════
//  AUTH
// ══════════════════════════════════════════════════════════════════════════════

export const authAPI = {
  login: async (email: string, password: string) => {
    // OAuth2 form requires urlencoded
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    const response = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new APIError(err.detail ?? 'Login failed', response.status);
    }
    return response.json();
  },
  me: () => api.get<User>('/auth/me'),
};


// ══════════════════════════════════════════════════════════════════════════════
//  PATIENTS
// ══════════════════════════════════════════════════════════════════════════════

export const patientAPI = {
  list:          ()                         => api.get<PatientListItem[]>('/patients'),
  get:           (id: string)               => api.get<Patient>(`/patients/${id}`),
  create:        (data: PatientCreate)      => api.post<Patient>('/patients', data),
  update:        (id: string, data: object) => api.patch<Patient>(`/patients/${id}`, data),
  getVitals:     (id: string)               => api.get<VitalSigns[]>(`/patients/${id}/vitals`),
  addVitals:     (id: string, data: object) => api.post<VitalSigns>(`/patients/${id}/vitals`, data),
  upsertICU:     (id: string, data: object) => api.put<ICUData>(`/patients/${id}/icu`, data),
  recordConsent: (id: string, by: string)   =>
    api.patch<{ success: boolean }>(`/patients/${id}/consent?consent_by=${encodeURIComponent(by)}`, {}),
};


// ══════════════════════════════════════════════════════════════════════════════
//  BRIEFINGS
// ══════════════════════════════════════════════════════════════════════════════

export const briefingAPI = {
  generate:  (payload: BriefingPayload)         => api.post<BriefingResponse>('/briefings/generate', payload),
  complete:  (data: BriefingCompleteData)        => api.post<BriefingOut>('/briefings/complete', data),
  listForPatient: (patientId: string)            => api.get<BriefingOut[]>(`/briefings/patient/${patientId}`),
};


// ══════════════════════════════════════════════════════════════════════════════
//  NOTES
// ══════════════════════════════════════════════════════════════════════════════

export const noteAPI = {
  generate:  (payload: NotePayload)             => api.post<NoteGenerateResponse>('/notes/generate', payload),
  approve:   (data: NoteApproveData)             => api.post<NoteOut>('/notes/approve', data),
  discharge: (patientId: string, data: object)   => api.post<NoteGenerateResponse>(`/notes/discharge/${patientId}`, data),
  listForPatient: (patientId: string)            => api.get<NoteOut[]>(`/notes/patient/${patientId}`),
};


// ══════════════════════════════════════════════════════════════════════════════
//  TYPES (mirrors backend schemas)
// ══════════════════════════════════════════════════════════════════════════════

export type User = {
  id: string;
  email: string;
  full_name: string;
  designation: string;
  registration_no?: string;
  role: string;
};

export type PatientListItem = {
  id: string;
  uhid: string;
  full_name: string;
  age: number;
  sex: string;
  ward?: string;
  bed_number?: string;
  primary_diagnosis?: string;
  trajectory: string;
  admitted_at: string;
  days_admitted: number;
  briefing_overdue: boolean;
  has_pending_results: boolean;
};

export type Patient = PatientListItem & {
  abha_id?: string;
  attending_consultant?: string;
  diagnosis_confirmed: boolean;
  last_briefing_at?: string;
  next_briefing_due?: string;
  ai_consent: boolean;
};

export type PatientCreate = {
  uhid: string;
  full_name: string;
  age: number;
  sex: string;
  admitted_at: string;
  ward?: string;
  bed_number?: string;
  primary_diagnosis?: string;
  attending_consultant?: string;
  ai_consent: boolean;
  ai_consent_by?: string;
};

export type VitalSigns = {
  id: string;
  recorded_at: string;
  sbp?: number; dbp?: number; map?: number;
  heart_rate?: number; spo2?: number; temperature?: number;
  respiratory_rate?: number; gcs?: number; urine_output_ml?: number;
  vasopressor_drug?: string; vasopressor_dose?: string; vasopressor_trend?: string;
};

export type ICUData = {
  ventilator_status: string;
  ventilator_mode?: string;
  fio2?: number; peep?: number;
  weaning_readiness?: string;
  estimated_extubation?: string;
};

export type BriefingPayload = {
  patient_id: string;
  trajectory: string;
  map_value?: number;
  heart_rate?: number;
  spo2?: number;
  gcs?: number;
  urine_output_4hr?: string;
  temperature?: number;
  vasopressor_drug?: string;
  vasopressor_dose?: string;
  vasopressor_trend?: string;
  ventilator_status?: string;
  ventilator_mode?: string;
  fio2?: number;
  peep?: number;
  weaning_readiness?: string;
  estimated_extubation?: string;
  key_lab_values?: LabValue[];
  imaging_summary?: string;
  procedure_done?: string;
  identified_risk_factors?: string[];
  specialists?: SpecialistInfo[];
  associate_notes?: string;
};

export type LabValue = {
  test_name: string;
  value: string;
  unit?: string;
  previous_value?: string;
  trend?: string;
  is_critical?: boolean;
};

export type SpecialistInfo = {
  name: string;
  specialty: string;
  last_review?: string;
  notes?: string;
};

export type BriefingResponse = {
  briefing_id: string;
  generated_at: string;
  document: BriefingDocument;
};

export type BriefingDocument = {
  trajectory_indicator: string;
  trajectory_label: string;
  q1_plain_language: string;
  q1_trajectory_statement: string;
  q1_do_not_say: string[];
  q1_clinical_summary: Record<string, string>;
  q2_plain_language: string;
  q2_treatment_items: { treatment: string; plain_explanation: string }[];
  q2_specialists: { name: string; specialty: string; last_review: string; status: string }[];
  q2_pending_reviews: string[];
  q3_plain_language: string;
  q3_conditional_phrases: Record<string, string>;
  q3_ventilator_assessment: Record<string, string>;
  q4_milestones: { step: number; description: string; status: string }[];
  q4_plain_language: string;
  q5_cause_plain: string;
  q5_escalation_prompt?: string;
  predicted_questions: { question: string; answer_framework: string; answer_full: string }[];
  key_numbers_panel: { label: string; value: string; status: string }[];
};

export type BriefingCompleteData = {
  briefing_id: string;
  family_members: { name: string; relationship: string }[];
  topics_covered: string[];
  questions_raised?: string;
  family_understanding: string;
  interpreter_used?: boolean;
  interpreter_language?: string;
  follow_up_promised?: string;
  duration_minutes?: number;
};

export type BriefingOut = {
  id: string;
  patient_id: string;
  status: string;
  created_at: string;
  completed_at?: string;
  topics_covered?: string[];
  family_members?: { name: string; relationship: string }[];
};

export type NotePayload = {
  patient_id: string;
  note_type: string;
  patient_complaints?: string;
  significant_events?: string;
  vitals?: Partial<VitalSigns> & { recorded_at: string };
  examination_findings?: string;
  new_lab_results?: LabValue[];
  imaging_results?: string;
  medication_changes?: string;
  diagnosis_status?: string;
  clinical_interpretation?: string;
  investigations_ordered?: string[];
  referrals_made?: string[];
  consultant_interactions?: { name: string; specialty: string; mode: string; recommendation: string }[];
  procedures_done?: string;
  nursing_instructions?: string;
  next_review_plan?: string;
  icu_data?: Partial<ICUData>;
};

export type SOAPNote = {
  note_type: string;
  subjective: string;
  objective_vitals?: string;
  objective_investigations?: string;
  assessment: string;
  plan: string;
  discussion?: string;
  next_review_trigger: string;
  quality_flags: string[];
};

export type NoteGenerateResponse = {
  note_id: string;
  soap_note: SOAPNote;
  generated_at: string;
  quality_flags: string[];
};

export type NoteApproveData = {
  note_id: string;
  subjective_override?: string;
  objective_override?: string;
  assessment_override?: string;
  plan_override?: string;
  discussion_override?: string;
};

export type NoteOut = {
  id: string;
  patient_id: string;
  note_type: string;
  status: string;
  subjective?: string;
  objective?: string;
  assessment?: string;
  plan?: string;
  discussion?: string;
  ai_generated: boolean;
  approved_at?: string;
  approved_by_name?: string;
  created_at: string;
};
