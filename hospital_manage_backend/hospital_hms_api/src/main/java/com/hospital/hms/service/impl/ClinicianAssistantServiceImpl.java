package com.hospital.hms.service.impl;

import com.hospital.hms.service.ClinicianAssistantService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;

@Service
public class ClinicianAssistantServiceImpl implements ClinicianAssistantService {

    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${patient-agent.base-url:http://localhost:8000}")
    private String patientAgentBaseUrl;

    @Override
    public HashMap<String, Object> chat(String message,
                                        String threadId,
                                        Integer userId,
                                        List<String> roleCodes,
                                        List<Integer> deptScope,
                                        List<Integer> doctorScope) {
        HashMap<String, Object> payload = new HashMap<>();
        payload.put("message", message);
        payload.put("threadId", threadId);
        payload.put("userId", userId);
        payload.put("roleCodes", roleCodes);
        payload.put("deptScope", deptScope);
        payload.put("doctorScope", doctorScope);

        return restTemplate.postForObject(
                patientAgentBaseUrl + "/api/clinician/chat",
                payload,
                HashMap.class
        );
    }
}
