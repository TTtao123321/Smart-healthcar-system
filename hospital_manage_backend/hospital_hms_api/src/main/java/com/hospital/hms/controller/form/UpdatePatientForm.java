package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;

@Schema(description = "修改患者信息表单")
@Data
public class UpdatePatientForm {

    @NotNull(message = "id不能为空")
    @Min(value = 1, message = "id不能小于1")
    private Integer id;

    @Pattern(regexp = "^[\\u4e00-\\u9fa5]{2,15}$", message = "name内容不正确")
    private String name;

    private String sex;

    private String pid;

    private String tel;

    private String birthday;

    private String medicalHistory;

    private String allergyHistory;

    private String familyHistory;

    private Integer insuranceType;
}
