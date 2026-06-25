package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import cn.hutool.core.bean.BeanUtil;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.InsertMedicalRegistrationForm;
import com.hospital.hms.pojo.MedicalRegistration;
import com.hospital.hms.service.MedicalRegistrationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;
import java.util.HashMap;

@RestController
@RequestMapping("/medical_registration")
@Tag(name = "MedicalRegistrationController", description = "挂号管理")
@Slf4j
public class MedicalRegistrationController {

    @Autowired
    private MedicalRegistrationService medicalRegistrationService;

    @PostMapping("/save")
    @Operation(summary = "创建挂号")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:INSERT"}, mode = SaMode.OR)
    public CommonResult save(@RequestBody @Valid InsertMedicalRegistrationForm form) {
        try {
            MedicalRegistration entity = new MedicalRegistration();
            BeanUtil.copyProperties(form, entity);
            int id = medicalRegistrationService.save(entity);
            HashMap<String, Object> result = new HashMap<>();
            result.put("id", id);
            result.put("status", 0);
            return CommonResult.ok().put("result", result);
        } catch (Exception e) {
            log.error("创建挂号失败, form:{}", form, e);
            return CommonResult.error("挂号失败！");
        }
    }
}
