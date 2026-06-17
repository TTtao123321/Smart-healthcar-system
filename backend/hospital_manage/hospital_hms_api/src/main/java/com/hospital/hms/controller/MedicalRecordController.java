package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import cn.hutool.core.bean.BeanUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.InsertMedicalRecordForm;
import com.hospital.hms.controller.form.SearchMedicalRecordForm;
import com.hospital.hms.controller.form.UpdateMedicalRecordForm;
import com.hospital.hms.pojo.MedicalRecord;
import com.hospital.hms.service.MedicalRecordService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/medical_record")
@Tag(name = "MedicalRecordController", description = "门诊病历管理")
@Slf4j
public class MedicalRecordController {

    @Autowired
    private MedicalRecordService medicalRecordService;

    @PostMapping("/insert")
    @Operation(summary = "添加门诊病历")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:INSERT"}, mode = SaMode.OR)
    public CommonResult insert(@RequestBody @Valid InsertMedicalRecordForm form) {
        try {
            MedicalRecord medicalRecord = new MedicalRecord();
            medicalRecord.setUuid(UUID.randomUUID().toString().replace("-", ""));
            BeanUtil.copyProperties(form, medicalRecord);
            int rows = medicalRecordService.insertMedicalRecord(medicalRecord);
            return CommonResult.ok().put("result", rows);
        } catch (Exception e) {
            log.error("添加门诊病历失败, form:{}", form, e);
            return CommonResult.error("添加失败！");
        }
    }

    @PostMapping("/update")
    @Operation(summary = "修改门诊病历")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:UPDATE"}, mode = SaMode.OR)
    public CommonResult update(@RequestBody @Valid UpdateMedicalRecordForm form) {
        try {
            MedicalRecord medicalRecord = new MedicalRecord();
            BeanUtil.copyProperties(form, medicalRecord);
            int rows = medicalRecordService.updateMedicalRecord(medicalRecord);
            return CommonResult.ok().put("result", rows);
        } catch (Exception e) {
            log.error("修改门诊病历失败, form:{}", form, e);
            return CommonResult.error("修改失败！");
        }
    }

    @PostMapping("/selectById")
    @Operation(summary = "根据ID查询门诊病历")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:SELECT"}, mode = SaMode.OR)
    public CommonResult selectById(@RequestBody Map<String, Integer> param) {
        try {
            MedicalRecord medicalRecord = medicalRecordService.selectById(param.get("id"));
            return CommonResult.ok().put("result", medicalRecord);
        } catch (Exception e) {
            log.error("查询门诊病历失败", e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/selectByRegistrationId")
    @Operation(summary = "根据挂号单ID查询门诊病历")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:SELECT"}, mode = SaMode.OR)
    public CommonResult selectByRegistrationId(@RequestBody Map<String, Integer> param) {
        try {
            MedicalRecord medicalRecord = medicalRecordService.selectByRegistrationId(param.get("registrationId"));
            return CommonResult.ok().put("result", medicalRecord);
        } catch (Exception e) {
            log.error("查询门诊病历失败", e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/selectByPatientId")
    @Operation(summary = "根据患者ID查询病历")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:SELECT"}, mode = SaMode.OR)
    public CommonResult selectByPatientId(@RequestBody Map<String, Integer> param) {
        try {
            Integer patientId = param.get("patientId");
            Integer deptSubId = param.get("deptSubId");
            Integer doctorId = param.get("doctorId");
            List<HashMap<String, Object>> list = medicalRecordService.selectByPatientId(patientId, deptSubId, doctorId);
            return CommonResult.ok().put("result", list);
        } catch (Exception e) {
            log.error("查询患者病历列表失败", e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/selectByPage")
    @Operation(summary = "分页查询门诊病历")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:SELECT"}, mode = SaMode.OR)
    public CommonResult selectByPage(@RequestBody @Valid SearchMedicalRecordForm form) {
        try {
            Map<String, Object> map = BeanUtil.beanToMap(form);
            PageUtils result = medicalRecordService.selectByPage(map);
            return CommonResult.ok().put("result", result);
        } catch (Exception e) {
            log.error("分页查询门诊病历失败, form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }
}
