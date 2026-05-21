package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import cn.hutool.core.bean.BeanUtil;
import cn.hutool.json.JSONUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.*;
import com.hospital.hms.pojo.MedicalDeptSub;
import com.hospital.hms.service.DeptSubService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.ArrayList;
import java.util.HashMap;

@RestController
@RequestMapping("/medical/dept/sub")
@Tag(name = "MedicalDeptSubController", description = "医疗诊室管理")
@Slf4j
public class DeptSubController {
    @Autowired
    private DeptSubService deptSubService;

    @PostMapping("/selectConditionByPage")
    @Operation(summary = "获取诊室信息")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL_DEPT_SUB:SELECT"}, mode = SaMode.OR)
    public CommonResult selectConditionByPage(@Valid @RequestBody SelectMedicalDeptSubByPageForm form){
        try {
            HashMap map = JSONUtil.parse(form).toBean(HashMap.class);
            PageUtils pageUtils = deptSubService.selectConditionByPage(map);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT, pageUtils);
        } catch (Exception e) {
            log.error("根据条件查询诊室信息失败,form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/insert")
    @Operation(summary = "添加诊室")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL_DEPT_SUB:INSERT"}, mode = SaMode.OR)
    public CommonResult insert(@Valid @RequestBody InsertMedicalDeptSubForm form){
        try {
            MedicalDeptSub deptSub = BeanUtil.toBean(form, MedicalDeptSub.class);
            deptSubService.insert(deptSub);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("添加诊室失败,form:{}", form, e);
            return CommonResult.error("添加失败！");
        }
    }

    @PostMapping("/selectById")
    @Operation(summary = "根据ID获取诊室信息")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL_DEPT_SUB:SELECT"}, mode = SaMode.OR)
    public CommonResult selectById(@Valid @RequestBody SelectMedicalDeptSubByIdForm form){
        try {
            Integer id = form.getId();
            HashMap map = deptSubService.selectById(id);
            return CommonResult.ok(map);
        } catch (Exception e) {
            log.error("回显诊室失败,form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/update")
    @Operation(summary = "更新诊室信息")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL_DEPT_SUB:UPDATE"}, mode = SaMode.OR)
    public CommonResult update(@Valid @RequestBody UpdateMedicalDeptSubForm form){
        try {
            MedicalDeptSub deptSub = BeanUtil.toBean(form, MedicalDeptSub.class);
            deptSubService.update(deptSub);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("更新诊室信息失败,form:{}", form, e);
            return CommonResult.error("修改失败！");
        }
    }

    @GetMapping("/selectByDeptId")
    @Operation(summary = "根据科室ID查询诊室列表")
    @SaCheckLogin
    public CommonResult selectByDeptId(Integer deptId) {
        try {
            ArrayList<HashMap> list = deptSubService.selectSubByDeptId(deptId);
            return CommonResult.ok().put("list", list);
        } catch (Exception e) {
            log.error("查询诊室列表失败, deptId:{}", deptId, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/deleteByIds")
    @Operation(summary = "删除诊室")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL_DEPT_SUB:DELETE"}, mode = SaMode.OR)
    public CommonResult deleteByIds(@Valid @RequestBody DeleteMedicalDeptSubByIdsForm form){
        try {
            Integer[] ids = form.getIds();
            deptSubService.deleteByIds(ids);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("删除诊室失败,form:{}", form, e);
            return CommonResult.error("删除失败！");
        }
    }
}
