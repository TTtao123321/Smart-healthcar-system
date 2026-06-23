package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotNull;

@Data
@Schema(description = "查询患者就诊记录表单")
public class SelectPatientRegistrationsForm {

    @NotNull(message = "patientCardId不能为空")
    @Min(value = 1, message = "patientCardId不能小于1")
    private Integer patientCardId;

    @Schema(description = "诊室ID，用于过滤同一科室诊室的记录")
    private Integer deptSubId;

    @Schema(description = "医生ID，用于过滤同一医生的记录")
    private Integer doctorId;
}
