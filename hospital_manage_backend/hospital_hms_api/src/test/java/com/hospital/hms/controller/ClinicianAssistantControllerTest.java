package com.hospital.hms.controller;

import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.ClinicianAssistantChatForm;
import com.hospital.hms.service.ClinicianAssistantService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.HashMap;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ClinicianAssistantControllerTest {

    @InjectMocks
    private ClinicianAssistantController clinicianAssistantController;

    @Mock
    private ClinicianAssistantService clinicianAssistantService;

    @Test
    @DisplayName("chat_转发医护上下文并返回临床通道")
    void chat_转发医护上下文并返回临床通道() {
        ClinicianAssistantChatForm form = new ClinicianAssistantChatForm();
        form.setMessage("查一下患者7的历史病历");
        form.setThreadId("thread-1");

        HashMap<String, Object> response = new HashMap<>();
        response.put("channel", "clinician");
        response.put("message", "临床回复");
        when(clinicianAssistantService.chat(
                "查一下患者7的历史病历",
                "thread-1",
                9,
                List.of("DOCTOR"),
                List.of(3),
                List.of(12)
        )).thenReturn(response);

        CommonResult result = clinicianAssistantController.chat(
                form,
                9,
                List.of("DOCTOR"),
                List.of(3),
                List.of(12)
        );

        assertEquals(200, result.get("code"));
        assertEquals("clinician", ((HashMap<?, ?>) result.get("result")).get("channel"));
        verify(clinicianAssistantService).chat(
                "查一下患者7的历史病历",
                "thread-1",
                9,
                List.of("DOCTOR"),
                List.of(3),
                List.of(12)
        );
    }
}
