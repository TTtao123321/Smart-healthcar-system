package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.Valid;
import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;
import java.util.List;

@Schema(description = "添加处方表单")
@Data
public class InsertPrescriptionForm {

    @NotNull(message = "medicalRecordId不能为空")
    private Integer medicalRecordId;

    @NotNull(message = "patientId不能为空")
    private Integer patientId;

    @NotNull(message = "doctorId不能为空")
    private Integer doctorId;

    private Integer type;

    @NotEmpty(message = "处方明细不能为空")
    @Valid
    private List<PrescriptionItemForm> items;

    @Data
    public static class PrescriptionItemForm {
        private String drugName;
        private String specification;
        private Integer quantity;
        private String dosage;
        private String frequency;
        private Integer days;
        private String remark;
    }
}
