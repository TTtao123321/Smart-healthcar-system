package com.hospital.hms.service.impl;

import com.hospital.hms.dao.PatientDao;
import com.hospital.hms.service.PatientResultService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

@Service
public class PatientResultServiceImpl implements PatientResultService {

    @Autowired
    private PatientDao patientDao;

    @Override
    public List<HashMap<String, Object>> selectPatientMedicalRecords(Integer patientId, String startDate, String endDate) {
        List<HashMap<String, Object>> rows = patientDao.selectPatientMedicalRecords(patientId, startDate, endDate);
        List<HashMap<String, Object>> results = new ArrayList<>();
        for (HashMap<String, Object> row : rows) {
            results.add(buildMedicalRecordListItem(row));
        }
        return results;
    }

    @Override
    public HashMap<String, Object> selectPatientMedicalRecordDetail(Integer patientId, Integer medicalRecordId) {
        HashMap<String, Object> row = patientDao.selectPatientMedicalRecordDetail(patientId, medicalRecordId);
        if (row == null) {
            return null;
        }
        return buildMedicalRecordDetail(row);
    }

    @Override
    public List<HashMap<String, Object>> selectPatientPrescriptions(Integer patientId, String startDate, String endDate) {
        List<HashMap<String, Object>> rows = patientDao.selectPatientPrescriptions(patientId, startDate, endDate);
        List<HashMap<String, Object>> results = new ArrayList<>();
        for (HashMap<String, Object> row : rows) {
            results.add(buildPrescriptionListItem(row));
        }
        return results;
    }

    @Override
    public HashMap<String, Object> selectPatientPrescriptionDetail(Integer patientId, Integer prescriptionId) {
        HashMap<String, Object> row = patientDao.selectPatientPrescriptionDetail(patientId, prescriptionId);
        if (row == null) {
            return null;
        }
        return buildPrescriptionDetail(row, patientDao.selectPatientPrescriptionItems(prescriptionId));
    }

    private HashMap<String, Object> buildMedicalRecordListItem(HashMap<String, Object> row) {
        HashMap<String, Object> result = new HashMap<>();
        result.put("medicalRecordId", row.get("medicalRecordId"));
        result.put("registrationId", row.get("registrationId"));
        result.put("visitDate", row.get("visitDate"));
        result.put("slot", row.get("slot"));
        result.put("department", row.get("department"));
        result.put("doctorName", row.get("doctorName"));
        result.put("chiefComplaintSummary", row.get("chiefComplaintSummary"));
        result.put("status", row.get("status"));
        return result;
    }

    private HashMap<String, Object> buildMedicalRecordDetail(HashMap<String, Object> row) {
        HashMap<String, Object> result = new HashMap<>();
        result.put("medicalRecordId", row.get("medicalRecordId"));
        result.put("registrationId", row.get("registrationId"));
        result.put("visitDate", row.get("visitDate"));
        result.put("slot", row.get("slot"));
        result.put("department", row.get("department"));
        result.put("doctorName", row.get("doctorName"));
        result.put("chiefComplaint", row.get("chiefComplaint"));
        result.put("diagnosisSummary", row.get("diagnosis"));
        result.put("instructionSummary", maskPatientVisibleText((String) row.get("doctorAdvice")));
        return result;
    }

    private HashMap<String, Object> buildPrescriptionListItem(HashMap<String, Object> row) {
        HashMap<String, Object> result = new HashMap<>();
        result.put("prescriptionId", row.get("prescriptionId"));
        result.put("medicalRecordId", row.get("medicalRecordId"));
        result.put("registrationId", row.get("registrationId"));
        result.put("visitDate", row.get("visitDate"));
        result.put("slot", row.get("slot"));
        result.put("department", row.get("department"));
        result.put("doctorName", row.get("doctorName"));
        result.put("type", row.get("type"));
        result.put("status", row.get("status"));
        result.put("createTime", row.get("createTime"));
        return result;
    }

    private HashMap<String, Object> buildPrescriptionDetail(HashMap<String, Object> row, List<HashMap<String, Object>> items) {
        HashMap<String, Object> result = new HashMap<>();
        result.put("prescriptionId", row.get("prescriptionId"));
        result.put("medicalRecordId", row.get("medicalRecordId"));
        result.put("registrationId", row.get("registrationId"));
        result.put("visitDate", row.get("visitDate"));
        result.put("slot", row.get("slot"));
        result.put("department", row.get("department"));
        result.put("doctorName", row.get("doctorName"));
        result.put("type", row.get("type"));
        result.put("status", row.get("status"));
        result.put("createTime", row.get("createTime"));
        result.put("diagnosis", row.get("diagnosis"));
        result.put("doctorAdvice", maskPatientVisibleText((String) row.get("doctorAdvice")));
        result.put("items", items);
        return result;
    }

    private String maskPatientVisibleText(String text) {
        if (text == null) {
            return null;
        }
        return text.replaceAll("，?医生内部备注[:：].*$", "");
    }
}
