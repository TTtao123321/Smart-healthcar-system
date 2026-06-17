package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import cn.hutool.core.bean.BeanUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.InsertPrescriptionForm;
import com.hospital.hms.pojo.Prescription;
import com.hospital.hms.pojo.PrescriptionItem;
import com.hospital.hms.service.PrescriptionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/prescription")
@Tag(name = "PrescriptionController", description = "处方管理")
@Slf4j
public class PrescriptionController {

    @Autowired
    private PrescriptionService prescriptionService;

    @PostMapping("/insert")
    @Operation(summary = "添加处方")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:INSERT"}, mode = SaMode.OR)
    public CommonResult insert(@RequestBody @Valid InsertPrescriptionForm form) {
        try {
            Prescription prescription = new Prescription();
            prescription.setUuid(UUID.randomUUID().toString().replace("-", ""));
            BeanUtil.copyProperties(form, prescription);
            prescription.setStatus(0);

            List<PrescriptionItem> items = new ArrayList<>();
            if (form.getItems() != null) {
                for (InsertPrescriptionForm.PrescriptionItemForm itemForm : form.getItems()) {
                    PrescriptionItem item = new PrescriptionItem();
                    BeanUtil.copyProperties(itemForm, item);
                    items.add(item);
                }
            }

            int rows = prescriptionService.insertPrescription(prescription, items);
            return CommonResult.ok().put("result", rows);
        } catch (Exception e) {
            log.error("添加处方失败, form:{}", form, e);
            return CommonResult.error("添加失败！");
        }
    }

    @PostMapping("/updateStatus")
    @Operation(summary = "更新处方状态")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:UPDATE"}, mode = SaMode.OR)
    public CommonResult updateStatus(@RequestBody Map<String, Integer> param) {
        try {
            Integer id = param.get("id");
            Integer status = param.get("status");
            int rows = prescriptionService.updatePrescriptionStatus(id, status);
            return CommonResult.ok().put("result", rows);
        } catch (Exception e) {
            log.error("更新处方状态失败", e);
            return CommonResult.error("更新失败！");
        }
    }

    @PostMapping("/selectByMedicalRecordId")
    @Operation(summary = "根据病历ID查处方")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:SELECT"}, mode = SaMode.OR)
    public CommonResult selectByMedicalRecordId(@RequestBody Map<String, Integer> param) {
        try {
            List<Map<String, Object>> list = prescriptionService.selectByMedicalRecordId(param.get("medicalRecordId"));
            return CommonResult.ok().put("result", list);
        } catch (Exception e) {
            log.error("查询处方失败", e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/selectItemsByPrescriptionId")
    @Operation(summary = "根据处方ID查明细")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:SELECT"}, mode = SaMode.OR)
    public CommonResult selectItemsByPrescriptionId(@RequestBody Map<String, Integer> param) {
        try {
            List<PrescriptionItem> items = prescriptionService.selectItemsByPrescriptionId(param.get("prescriptionId"));
            return CommonResult.ok().put("result", items);
        } catch (Exception e) {
            log.error("查询处方明细失败", e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/selectByPatientId")
    @Operation(summary = "根据患者ID分页查处方")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:SELECT"}, mode = SaMode.OR)
    public CommonResult selectByPatientId(@RequestBody Map<String, Object> param) {
        try {
            PageUtils result = prescriptionService.selectByPatientId(param);
            return CommonResult.ok().put("result", result);
        } catch (Exception e) {
            log.error("查询患者处方失败", e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/deleteById")
    @Operation(summary = "删除处方")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL:DELETE"}, mode = SaMode.OR)
    public CommonResult deleteById(@RequestBody Map<String, Integer> param) {
        try {
            Integer id = param.get("id");
            if (id == null) {
                return CommonResult.error("参数不完整！");
            }
            int rows = prescriptionService.deletePrescriptionById(id);
            return CommonResult.ok().put("result", rows);
        } catch (Exception e) {
            log.error("删除处方失败", e);
            return CommonResult.error("删除失败！");
        }
    }
}
