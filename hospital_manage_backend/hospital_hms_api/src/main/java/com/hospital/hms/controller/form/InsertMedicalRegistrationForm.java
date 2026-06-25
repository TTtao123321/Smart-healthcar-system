package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import org.hibernate.validator.constraints.Range;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

@Data
@Schema(description = "创建挂号表单")
public class InsertMedicalRegistrationForm {

    @NotNull(message = "patientCardId不能为空")
    @Min(value = 1, message = "patientCardId不能小于1")
    private Integer patientCardId;

    @NotNull(message = "workPlanId不能为空")
    @Min(value = 1, message = "workPlanId不能小于1")
    private Integer workPlanId;

    @NotNull(message = "doctorScheduleId不能为空")
    @Min(value = 1, message = "doctorScheduleId不能小于1")
    private Integer doctorScheduleId;

    @NotNull(message = "doctorId不能为空")
    @Min(value = 1, message = "doctorId不能小于1")
    private Integer doctorId;

    @NotNull(message = "deptSubId不能为空")
    @Min(value = 1, message = "deptSubId不能小于1")
    private Integer deptSubId;

    @NotBlank(message = "date不能为空")
    private String date;

    @NotNull(message = "slot不能为空")
    @Range(min = 1, max = 15, message = "slot内容不正确")
    private Integer slot;
}
