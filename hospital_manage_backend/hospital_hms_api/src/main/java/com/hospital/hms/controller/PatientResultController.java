package com.hospital.hms.controller;

import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.SelectPatientMedicalRecordDetailForm;
import com.hospital.hms.controller.form.SelectPatientMedicalRecordsForm;
import com.hospital.hms.controller.form.SelectPatientPrescriptionDetailForm;
import com.hospital.hms.controller.form.SelectPatientPrescriptionsForm;
import com.hospital.hms.service.PatientResultService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;

@RestController
@RequestMapping("/patient")
@Tag(name = "PatientResultController", description = "患者结果查询")
@Slf4j
public class PatientResultController {

    @Autowired
    private PatientResultService patientResultService;

    @PostMapping("/medical-records")
    @Operation(summary = "查询患者病历列表")
    public CommonResult selectMedicalRecords(@RequestBody @Valid SelectPatientMedicalRecordsForm form) {
        try {
            return CommonResult.ok().put("result",
                    patientResultService.selectPatientMedicalRecords(
                            form.getPatientId(),
                            form.getStartDate(),
                            form.getEndDate()
                    ));
        } catch (Exception e) {
            log.error("查询患者病历列表失败, form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/medical-records/detail")
    @Operation(summary = "查询患者病历详情")
    public CommonResult selectMedicalRecordDetail(@RequestBody @Valid SelectPatientMedicalRecordDetailForm form) {
        try {
            return CommonResult.ok().put("result",
                    patientResultService.selectPatientMedicalRecordDetail(
                            form.getPatientId(),
                            form.getMedicalRecordId()
                    ));
        } catch (Exception e) {
            log.error("查询患者病历详情失败, form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/prescriptions")
    @Operation(summary = "查询患者处方列表")
    public CommonResult selectPrescriptions(@RequestBody @Valid SelectPatientPrescriptionsForm form) {
        try {
            return CommonResult.ok().put("result",
                    patientResultService.selectPatientPrescriptions(
                            form.getPatientId(),
                            form.getStartDate(),
                            form.getEndDate()
                    ));
        } catch (Exception e) {
            log.error("查询患者处方列表失败, form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/prescriptions/detail")
    @Operation(summary = "查询患者处方详情")
    public CommonResult selectPrescriptionDetail(@RequestBody @Valid SelectPatientPrescriptionDetailForm form) {
        try {
            return CommonResult.ok().put("result",
                    patientResultService.selectPatientPrescriptionDetail(
                            form.getPatientId(),
                            form.getPrescriptionId()
                    ));
        } catch (Exception e) {
            log.error("查询患者处方详情失败, form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }
}
