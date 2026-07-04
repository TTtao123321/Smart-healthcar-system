package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotNull;

@Data
@Schema(description = "查询患者处方详情表单")
public class SelectPatientPrescriptionDetailForm {

    @NotNull(message = "patientId不能为空")
    @Min(value = 1, message = "patientId不能小于1")
    private Integer patientId;

    @NotNull(message = "prescriptionId不能为空")
    @Min(value = 1, message = "prescriptionId不能小于1")
    private Integer prescriptionId;
}
