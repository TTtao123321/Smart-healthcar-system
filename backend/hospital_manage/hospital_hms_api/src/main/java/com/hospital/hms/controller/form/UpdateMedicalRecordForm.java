package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotNull;

@Schema(description = "修改门诊病历表单")
@Data
public class UpdateMedicalRecordForm {

    @NotNull(message = "id不能为空")
    private Integer id;

    private String chiefComplaint;

    private String presentIllness;

    private String physicalExam;

    private String diagnosis;

    private String doctorAdvice;

    private String remark;
}
