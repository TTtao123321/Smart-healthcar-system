package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.util.IdUtil;
import cn.hutool.json.JSONUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.*;
import com.hospital.hms.service.DoctorService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.repository.query.Param;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.validation.Valid;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/doctor")
@Tag(name = "DoctorController", description = "医生信息管理")
@Slf4j
public class DoctorController {
    @Autowired
    private DoctorService doctorService;

    @PostMapping("/selectConditionByPage")
    @Operation(summary = "获取医生信息")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR:SELECT"}, mode = SaMode.OR)
    public CommonResult selectConditionByPage(@RequestBody @Valid SelectDoctorByPageForm form){
        try {
            Map<String, Object> map = BeanUtil.beanToMap(form);
            PageUtils result = doctorService.selectConditionByPage(map);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT,result);
        } catch (Exception e) {
            log.error("查询医生信息失败,form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/insert")
    @Operation(summary = "添加医生")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR:INSERT"}, mode = SaMode.OR)
    public CommonResult insert(@RequestBody @Valid InsertDoctorForm form){
        try {
            Map<String, Object> map = BeanUtil.beanToMap(form);
            String json = JSONUtil.parseArray(form.getTag()).toString();
            map.replace("tag",json);
            map.put("uuid", IdUtil.simpleUUID().toUpperCase());
            doctorService.insert(map);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("添加医生失败,form:{}", form, e);
            return CommonResult.error("添加失败！");
        }
    }

    @PostMapping("/selectById")
    @Operation(summary = "根据ID查询医生信息")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR:SELECT"}, mode = SaMode.OR)
    public CommonResult selectById(@RequestBody @Valid SelectDoctorByIdForm form){
        try {
            Integer id = form.getId();
            HashMap result = doctorService.selectById(id);
            return CommonResult.ok(result);
        } catch (Exception e) {
            log.error("回显医生信息失败,form:{}", form, e);
            return CommonResult.error("回显失败！");
        }
    }

    @PostMapping("/update")
    @Operation(summary = "更新医生信息")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR:UPDATE"}, mode = SaMode.OR)
    public CommonResult update(@RequestBody @Valid UpdateDoctorForm form){
        try {
            Map<String, Object> param = BeanUtil.beanToMap(form);
            String json = JSONUtil.parseArray(form.getTag()).toString();
            param.replace("tag", json);
            doctorService.update(param);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("更新医生信息失败,form:{}", form, e);
            return CommonResult.error("修改失败！");
        }
    }

    @PostMapping("/deleteDoctorByIds")
    @Operation(summary = "删除医生")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR:DELETE"}, mode = SaMode.OR)
    public CommonResult deleteDoctorByIds(@RequestBody @Valid DeleteDoctorByIdsForm form){
        try {
            Integer[] ids = form.getIds();
            doctorService.deleteDoctorByIds(ids);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("删除医生失败,form:{}", form, e);
            return CommonResult.error("删除失败！");
        }
    }

    @PostMapping("/selectDoctorDetailById")
    @Operation(summary = "查询医生详细信息")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR:SELECT"}, mode = SaMode.OR)
    public CommonResult selectDoctorDetailById(@RequestBody @Valid SelectDoctorDetailByIdForm form){
        try {
            Integer id = form.getId();
            HashMap result = doctorService.selectDoctorDetailById(id);
            return CommonResult.ok().put("doctor",result);
        } catch (Exception e) {
            log.error("查找医生信息失败,form:{}", form, e);
            return CommonResult.error("查找失败！");
        }
    }

    @PostMapping("/updatePhoto")
    @Operation(summary = "更新医生头像")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR:UPDATE"}, mode = SaMode.OR)
    public CommonResult upupdatePhoto(@Param("file") MultipartFile file, @Param("doctorId") Integer doctorId){
        try {
            doctorService.updatePhoto(file,doctorId);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("更新医生头像失败,doctorId:{}", doctorId, e);
            return CommonResult.error("修改失败！");
        }
    }

    @PostMapping("/selectDoctorsBySubId")
    @Operation(summary = "根据诊室查找医生")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR:SELECT"}, mode = SaMode.OR)
    public CommonResult selectDoctorsBySubId(@RequestBody @Valid SelectDoctorsBySubIdForm form){
        try {
            Integer deptSubId = form.getDeptSubId();
            ArrayList<HashMap> doctors = doctorService.selectDoctorsBySubId(deptSubId);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT,doctors);
        } catch (Exception e) {
            log.error("查找医生失败,form:{}", form, e);
            return CommonResult.error("查找失败！");
        }
    }
}
