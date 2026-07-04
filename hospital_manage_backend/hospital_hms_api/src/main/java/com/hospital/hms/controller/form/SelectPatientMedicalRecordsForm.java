package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotNull;

@Data
@Schema(description = "查询患者病历列表表单")
public class SelectPatientMedicalRecordsForm {

    @NotNull(message = "patientId不能为空")
    @Min(value = 1, message = "patientId不能小于1")
    private Integer patientId;

    @Schema(description = "开始日期，格式 yyyy-MM-dd")
    private String startDate;

    @Schema(description = "结束日期，格式 yyyy-MM-dd")
    private String endDate;
}
