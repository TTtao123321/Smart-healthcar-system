package com.hospital.hms.event;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ScheduleEventPayload {
    private Integer workPlanId;
    private List<Integer> affectedScheduleIds;
    private String changeType;
    private Map<String, Object> before;
    private Map<String, Object> after;
    private List<Integer> affectedPatientIds;
}
