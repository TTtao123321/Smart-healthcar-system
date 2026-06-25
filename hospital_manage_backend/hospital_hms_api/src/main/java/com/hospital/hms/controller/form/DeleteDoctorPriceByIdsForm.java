package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;

@Schema(description = "删除诊费表单")
@Data
public class DeleteDoctorPriceByIdsForm {

    @NotEmpty(message = "ids不能为空")
    @Schema(description = "诊费ID")
    private Integer[] ids;
}
