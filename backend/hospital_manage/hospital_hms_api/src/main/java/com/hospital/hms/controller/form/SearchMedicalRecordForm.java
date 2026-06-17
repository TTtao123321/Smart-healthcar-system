package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "查询门诊病历表单")
@Data
public class SearchMedicalRecordForm {

    private Integer patientId;
    private Integer doctorId;
    private Integer registrationId;
    private Integer page;
    private Integer length;
}
