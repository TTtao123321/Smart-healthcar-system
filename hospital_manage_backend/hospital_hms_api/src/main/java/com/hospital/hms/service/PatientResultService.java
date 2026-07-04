package com.hospital.hms.service;

import java.util.HashMap;
import java.util.List;

public interface PatientResultService {

    List<HashMap<String, Object>> selectPatientMedicalRecords(Integer patientId, String startDate, String endDate);

    HashMap<String, Object> selectPatientMedicalRecordDetail(Integer patientId, Integer medicalRecordId);

    List<HashMap<String, Object>> selectPatientPrescriptions(Integer patientId, String startDate, String endDate);

    HashMap<String, Object> selectPatientPrescriptionDetail(Integer patientId, Integer prescriptionId);
}
