package com.hospital.hms.controller.form;

import lombok.Data;

import javax.validation.constraints.NotBlank;

@Data
public class ClinicianAssistantChatForm {
    @NotBlank(message = "message不能为空")
    private String message;

    private String threadId;
}
