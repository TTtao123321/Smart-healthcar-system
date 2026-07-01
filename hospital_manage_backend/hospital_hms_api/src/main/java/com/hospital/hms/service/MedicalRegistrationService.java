package com.hospital.hms.service;

import com.hospital.hms.pojo.MedicalRegistration;

public interface MedicalRegistrationService {
    int save(MedicalRegistration entity);

    int cancelRegistration(Integer registrationId);
}
