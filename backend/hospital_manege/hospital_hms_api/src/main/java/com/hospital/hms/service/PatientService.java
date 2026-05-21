package com.hospital.hms.service;

import com.hospital.common.utils.PageUtils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public interface PatientService {

    PageUtils selectPatientByPage(Map<String, Object> map);

    HashMap<String, Object> selectPatientDetail(Integer patientCardId);
}
