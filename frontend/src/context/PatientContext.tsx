/**
 * AC Agent — Patient Context
 * Caches the active patient list and selected patient.
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { patientAPI, PatientListItem, Patient } from '../services/api';

type PatientState = {
  patients: PatientListItem[];
  selectedPatient: Patient | null;
  isLoadingList: boolean;
  isLoadingDetail: boolean;
  fetchPatients: () => Promise<void>;
  selectPatient: (id: string) => Promise<void>;
  clearSelection: () => void;
  refreshPatient: (id: string) => Promise<void>;
};

const PatientContext = createContext<PatientState | null>(null);

export function PatientProvider({ children }: { children: ReactNode }) {
  const [patients, setPatients] = useState<PatientListItem[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const fetchPatients = useCallback(async () => {
    setIsLoadingList(true);
    try {
      const data = await patientAPI.list();
      setPatients(data);
    } finally {
      setIsLoadingList(false);
    }
  }, []);

  const selectPatient = useCallback(async (id: string) => {
    setIsLoadingDetail(true);
    try {
      const data = await patientAPI.get(id);
      setSelectedPatient(data);
    } finally {
      setIsLoadingDetail(false);
    }
  }, []);

  const refreshPatient = useCallback(async (id: string) => {
    const data = await patientAPI.get(id);
    setSelectedPatient(data);
  }, []);

  const clearSelection = () => setSelectedPatient(null);

  return (
    <PatientContext.Provider value={{
      patients, selectedPatient, isLoadingList, isLoadingDetail,
      fetchPatients, selectPatient, clearSelection, refreshPatient,
    }}>
      {children}
    </PatientContext.Provider>
  );
}

export const usePatients = () => {
  const ctx = useContext(PatientContext);
  if (!ctx) throw new Error('usePatients must be inside PatientProvider');
  return ctx;
};
