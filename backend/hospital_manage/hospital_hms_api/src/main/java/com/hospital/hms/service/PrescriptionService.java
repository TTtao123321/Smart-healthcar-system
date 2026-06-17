package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;
import com.hospital.hms.pojo.Prescription;
import com.hospital.hms.pojo.PrescriptionItem;

import java.util.List;
import java.util.Map;

public interface PrescriptionService {

    int insertPrescription(Prescription prescription, List<PrescriptionItem> items);

    int updatePrescriptionStatus(Integer id, Integer status);

    Prescription selectById(Integer id);

    List<Map<String, Object>> selectByMedicalRecordId(Integer medicalRecordId);

    PageUtils selectByPatientId(Map<String, Object> map);

    List<PrescriptionItem> selectItemsByPrescriptionId(Integer prescriptionId);

    int deletePrescriptionById(Integer id);
}
