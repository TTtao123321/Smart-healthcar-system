package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.stp.StpUtil;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.ClinicianAssistantChatForm;
import com.hospital.hms.service.ClinicianAssistantService;
import com.hospital.hms.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

@RestController
@RequestMapping("/clinician-assistant")
@Tag(name = "ClinicianAssistantController", description = "医护端智能助手")
@Slf4j
public class ClinicianAssistantController {

    @Autowired
    private ClinicianAssistantService clinicianAssistantService;

    @Autowired
    private UserService userService;

    @PostMapping("/chat")
    @Operation(summary = "医护端智能助手对话")
    @SaCheckLogin
    public CommonResult chat(@RequestBody @Valid ClinicianAssistantChatForm form) {
        Integer userId = Integer.parseInt(StpUtil.getLoginId().toString());
        List<String> roles = new ArrayList<>(userService.selectUserRoleNames(userId));
        return chat(form, userId, roles, List.of(), List.of());
    }

    public CommonResult chat(ClinicianAssistantChatForm form,
                             Integer userId,
                             List<String> roleCodes,
                             List<Integer> deptScope,
                             List<Integer> doctorScope) {
        try {
            HashMap<String, Object> result = clinicianAssistantService.chat(
                    form.getMessage(),
                    form.getThreadId(),
                    userId,
                    roleCodes,
                    deptScope,
                    doctorScope
            );
            return CommonResult.ok().put("result", result);
        } catch (Exception e) {
            log.error("医护端智能助手调用失败, form:{}", form, e);
            return CommonResult.error("调用失败！");
        }
    }
}
