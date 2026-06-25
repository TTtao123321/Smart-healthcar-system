package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;
import java.math.BigDecimal;

@Schema(description = "更新诊费表单")
@Data
public class UpdateDoctorPriceForm {

    @NotNull(message = "id不能为空")
    @Min(value = 1, message = "id不能小于1")
    @Schema(description = "诊费ID")
    private Integer id;

    @NotBlank(message = "level不能为空")
    @Pattern(regexp = "^主治医师$|^副主治医师$|^主任医师$|^副主任医师$", message = "level内容不正确")
    @Schema(description = "职称级别")
    private String level;

    @NotNull(message = "price_1不能为空")
    @Schema(description = "门诊挂号费")
    private BigDecimal price_1;

    @NotNull(message = "price_2不能为空")
    @Schema(description = "视频问诊挂号费")
    private BigDecimal price_2;
}
