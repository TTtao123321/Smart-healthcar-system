package com.hospital.hms.controller.form;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Pattern;

@Schema(description = "修改用户密码")
@Data
public class UpdateUserPasswordForm {
    @Schema(description = "旧密码")
    @NotBlank(message = "密码不能为空")
    @Pattern(regexp = "^[a-zA-Z0-9]{4,15}$",message = "密码不符合格式要求")
    private String oldPassword;

    @Schema(description = "新密码")
    @NotBlank(message = "密码不能为空")
    @Pattern(regexp = "^[a-zA-Z0-9]{4,15}$",message = "密码不符合格式要求")
    private String newPassword;
}