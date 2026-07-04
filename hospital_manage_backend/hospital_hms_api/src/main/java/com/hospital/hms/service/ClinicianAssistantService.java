package com.hospital.hms.service;

import java.util.HashMap;
import java.util.List;

public interface ClinicianAssistantService {
    HashMap<String, Object> chat(String message,
                                 String threadId,
                                 Integer userId,
                                 List<String> roleCodes,
                                 List<Integer> deptScope,
                                 List<Integer> doctorScope);
}
