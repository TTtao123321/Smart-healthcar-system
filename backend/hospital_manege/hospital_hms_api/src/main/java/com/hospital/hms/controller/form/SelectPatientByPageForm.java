package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import org.hibernate.validator.constraints.Range;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;

@Data
@Schema(description = "查询患者分页表单")
public class SelectPatientByPageForm {

    @Pattern(regexp = "^[\\u4e00-\\u9fa5]{1,20}$", message = "name内容不正确")
    private String name;

    @Pattern(regexp = "^男$|^女$", message = "sex内容不正确")
    private String sex;

    @Min(value = 1, message = "deptId不能小于1")
    private Integer deptId;

    @Min(value = 1, message = "deptSubId不能小于1")
    private Integer deptSubId;

    @Min(value = 1, message = "doctorId不能小于1")
    private Integer doctorId;

    @Range(min = 0, max = 3, message = "status内容不正确")
    private Integer status;

    @NotNull(message = "page不能为空")
    @Min(value = 1, message = "page不能小于1")
    private Integer page;

    @NotNull(message = "length不能为空")
    @Range(min = 10, max = 50, message = "length内容不正确")
    private Integer length;
}
