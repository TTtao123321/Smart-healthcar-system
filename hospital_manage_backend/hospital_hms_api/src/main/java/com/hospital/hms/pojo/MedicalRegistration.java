package com.hospital.hms.pojo;

import lombok.Data;

@Data
public class MedicalRegistration {
    private Integer id;
    private Integer patientCardId;
    private Integer workPlanId;
    private Integer doctorScheduleId;
    private Integer doctorId;
    private Integer deptSubId;
    private String date;
    private Integer slot;
    private Integer status;
    private Integer paymentStatus;
}
