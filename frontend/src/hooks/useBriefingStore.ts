/**
 * AC Agent — Briefing Store Hook
 * In-memory store for the current briefing document during a session.
 */

import { useState, useCallback } from 'react';
import { BriefingDocument } from '../services/api';

// Simple module-level cache (session only — no persistence needed)
const _store: Record<string, { document: BriefingDocument; patientName: string }> = {};

export function storeBriefing(briefingId: string, document: BriefingDocument, patientName: string) {
  _store[briefingId] = { document, patientName };
}

export function useBriefingStore(briefingId: string) {
  return _store[briefingId] ?? { document: null, patientName: '' };
}

// Note store
const _noteStore: Record<string, any> = {};

export function storeNote(noteId: string, soapNote: any, patientId: string) {
  _noteStore[noteId] = { soapNote, patientId };
}

export function useNoteStore(noteId: string) {
  return _noteStore[noteId] ?? { soapNote: null, patientId: '' };
}
