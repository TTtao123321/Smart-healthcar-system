package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import cn.hutool.core.bean.BeanUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.*;
import com.hospital.hms.pojo.MedicalDept;
import com.hospital.hms.service.DeptService;
import io.swagger.v3.oas.annotations.Operation;
//import io.swagger.v3.oas.annotations.parameters.RequestBody;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/medical/dept")
@Tag(name = "MedicalDeptController",description = "医疗科室管理接口")
@Slf4j
public class DeptController {
    @Autowired
    private DeptService deptService;

    @PostMapping("/selectConditionByPage")
    @Operation(summary = "根据条件查询科室信息")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL_DEPT:SELECT"}, mode = SaMode.OR)
    public CommonResult selectConditionByPage(@RequestBody @Valid SelectMedicalDeptByPageForm form) {
        try {
            Map<String, Object> map = BeanUtil.beanToMap(form);
            PageUtils result = deptService.selectConditionByPage(map);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT,result);
        } catch (Exception e) {
            log.error("根据条件查询科室信息失败,form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/insert")
    @Operation(summary = "添加科室信息接口")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL_DEPT:INSERT"}, mode = SaMode.OR)
    public CommonResult insert(@Valid @RequestBody InsertMedicalDeptForm form){
        try {
            MedicalDept dept = BeanUtil.toBean(form, MedicalDept.class);
            deptService.insert(dept);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("添加科室失败,form:{}", form, e);
            return CommonResult.error("添加失败！");
        }
    }

    @PostMapping("/selectById")
    @Operation(summary = "根据ID查询科室信息")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL_DEPT:INSERT"}, mode = SaMode.OR)
    public CommonResult selectById(@Valid @RequestBody SelectMedicalDeptByIdForm form){
        try {
            Integer id = form.getId();
            HashMap map = deptService.selectById(id);
            return CommonResult.ok(map);
        } catch (Exception e) {
            log.error("查询科室信息失败,form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/update")
    @Operation(summary = "更新科室信息")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL_DEPT:UPDATE"}, mode = SaMode.OR)
    public CommonResult update(@Valid @RequestBody UpdateMedicalDeptForm form){
        try {
            MedicalDept dept = BeanUtil.toBean(form, MedicalDept.class);
            deptService.update(dept);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("更新科室信息失败,form:{}", form, e);
            return CommonResult.error("更新失败！");
        }
    }

    @PostMapping("/deleteByIds")
    @Operation(summary = "删除科室")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "MEDICAL_DEPT:DELETE"}, mode = SaMode.OR)
    public CommonResult deleteByIds(@RequestBody @Valid DeleteMedicalDeptByIdsForm form){
        try {
            Integer[] ids = form.getIds();
            deptService.deleteByIds(ids);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("删除科室失败,form:{}", form, e);
            return CommonResult.error("删除失败！");
        }
    }

    @GetMapping("/selectAllDeptNameAndId")
    @Operation(summary = "获取所有科室名称和id")
    @SaCheckLogin
    public CommonResult selectAllDeptNameAndId(){
        ArrayList<HashMap> result = deptService.selectAllDeptNameAndId();
        return CommonResult.ok().put(CommonResult.RETURN_RESULT, result);
    }

    @GetMapping("/selectDeptAndSub")
    @Operation(summary = "获取所有科室和诊室")
    @SaCheckLogin
    public CommonResult selectDeptAndSub(){
        HashMap result = deptService.selectDeptAndSub();
        return CommonResult.ok().put(CommonResult.RETURN_RESULT, result);
    }
}
