package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

@Schema(description = "添加门诊病历表单")
@Data
public class InsertMedicalRecordForm {

    @NotNull(message = "registrationId不能为空")
    private Integer registrationId;

    @NotNull(message = "patientId不能为空")
    private Integer patientId;

    @NotNull(message = "doctorId不能为空")
    private Integer doctorId;

    private Integer deptSubId;

    @NotBlank(message = "chiefComplaint不能为空")
    private String chiefComplaint;

    private String presentIllness;

    private String physicalExam;

    private String diagnosis;

    private String doctorAdvice;

    private String remark;
}
