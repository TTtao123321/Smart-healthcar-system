package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import cn.hutool.core.bean.BeanUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.SelectPatientByPageForm;
import com.hospital.hms.controller.form.SelectPatientRegistrationsForm;
import com.hospital.hms.service.PatientService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/patient")
@Tag(name = "PatientController", description = "患者管理")
@Slf4j
public class PatientController {

    @Autowired
    private PatientService patientService;

    @PostMapping("/selectByPage")
    @Operation(summary = "分页查询患者就诊记录")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:SELECT"}, mode = SaMode.OR)
    public CommonResult selectByPage(@RequestBody @Valid SelectPatientByPageForm form) {
        try {
            Map<String, Object> map = BeanUtil.beanToMap(form);
            PageUtils result = patientService.selectPatientByPage(map);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, result);
        } catch (Exception e) {
            log.error("查询患者列表失败, form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/selectDetail")
    @Operation(summary = "查询患者详情和就诊记录")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:SELECT"}, mode = SaMode.OR)
    public CommonResult selectDetail(@RequestBody @Valid SelectPatientRegistrationsForm form) {
        try {
            HashMap<String, Object> result = patientService.selectPatientDetail(form.getPatientCardId());
            return CommonResult.ok(result);
        } catch (Exception e) {
            log.error("查询患者详情失败, form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }
}
