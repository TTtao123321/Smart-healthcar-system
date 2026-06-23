package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import cn.hutool.core.bean.BeanUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.InsertPatientUserInfoForm;
import com.hospital.hms.controller.form.SelectPatientByPageForm;
import com.hospital.hms.controller.form.SelectPatientRegistrationsForm;
import com.hospital.hms.controller.form.UpdatePatientForm;
import com.hospital.hms.pojo.PatientUserInfo;
import com.hospital.hms.service.PatientService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

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
            HashMap<String, Object> result = patientService.selectPatientDetail(
                    form.getPatientCardId(), form.getDeptSubId(), form.getDoctorId());
            return CommonResult.ok(result);
        } catch (Exception e) {
            log.error("查询患者详情失败, form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/insert")
    @Operation(summary = "添加患者")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:INSERT"}, mode = SaMode.OR)
    public CommonResult insert(@RequestBody @Valid InsertPatientUserInfoForm form) {
        try {
            PatientUserInfo patient = new PatientUserInfo();
            patient.setUuid(UUID.randomUUID().toString().replace("-", ""));
            BeanUtil.copyProperties(form, patient);
            int rows = patientService.insertPatient(patient);
            return CommonResult.ok().put("result", rows);
        } catch (Exception e) {
            log.error("添加患者失败, form:{}", form, e);
            return CommonResult.error("添加失败！");
        }
    }

    @PostMapping("/update")
    @Operation(summary = "修改患者信息")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:UPDATE"}, mode = SaMode.OR)
    public CommonResult update(@RequestBody @Valid UpdatePatientForm form) {
        try {
            PatientUserInfo patient = new PatientUserInfo();
            BeanUtil.copyProperties(form, patient);
            int rows = patientService.updatePatient(patient);
            return CommonResult.ok().put("result", rows);
        } catch (Exception e) {
            log.error("修改患者信息失败, form:{}", form, e);
            return CommonResult.error("修改失败！");
        }
    }

    @PostMapping("/updateRegistrationStatus")
    @Operation(summary = "更新挂号状态")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:UPDATE"}, mode = SaMode.OR)
    public CommonResult updateRegistrationStatus(@RequestBody Map<String, Integer> param) {
        try {
            Integer id = param.get("id");
            Integer status = param.get("status");
            if (id == null || status == null) {
                return CommonResult.error("参数不完整！");
            }
            int rows = patientService.updateRegistrationStatus(id, status);
            return CommonResult.ok().put("result", rows);
        } catch (Exception e) {
            log.error("更新挂号状态失败", e);
            return CommonResult.error("更新失败！");
        }
    }

}
