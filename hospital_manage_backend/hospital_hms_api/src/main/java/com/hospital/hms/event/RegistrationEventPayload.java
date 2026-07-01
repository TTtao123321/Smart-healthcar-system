package com.hospital.hms.event;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class RegistrationEventPayload {
    private Integer registrationId;
    private Integer patientId;
    private Integer workPlanId;
    private Integer doctorScheduleId;
    private Integer doctorId;
    private Integer deptSubId;
    private String date;
    private Integer slot;
}
