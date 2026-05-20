package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import cn.hutool.core.bean.BeanUtil;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.controller.form.DeleteWorkPlanForm;
import com.hospital.hms.controller.form.SelectScheduleByDeptSubForm;
import com.hospital.hms.controller.form.SelectScheduleByWorkPlanIdForm;
import com.hospital.hms.controller.form.UpdateDoctorScheduleForm;
import com.hospital.hms.service.DoctorWorkPlanScheduleService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/doctor/work_plan/schedule")
@Tag(name = "DoctorWorkPlanController", description = "医生出诊计划管理")
@Slf4j
public class DoctorWorkPlanScheduleController {
    @Autowired
    private DoctorWorkPlanScheduleService doctorWorkPlanScheduleService;

    @PostMapping("/selectDoctorScheduleByDeptSubIdAndDate")
    @Operation(summary = "查询医生出诊计划")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR_WORK_PLAN_SCHEDULE:SELECT"}, mode = SaMode.OR)
    public CommonResult selectDoctorScheduleByDeptSubIdAndDate(@RequestBody @Valid SelectScheduleByDeptSubForm form){
        try {
            Map<String, Object> map = BeanUtil.beanToMap(form);
            ArrayList<HashMap> result = doctorWorkPlanScheduleService.selectDoctorScheduleByDeptSubIdAndDate(map);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT,result);
        } catch (Exception e) {
            log.error("查询出诊计划出错，form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/selectScheduleByWorkPlanId")
    @Operation(summary = "查询指定医生出诊计划")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR_WORK_PLAN_SCHEDULE:SELECT"}, mode = SaMode.OR)
    public CommonResult selectScheduleByWorkPlanId(@RequestBody @Valid SelectScheduleByWorkPlanIdForm form){
        try {
            Integer workPlanId = form.getWorkPlanId();
            HashMap result = doctorWorkPlanScheduleService.selectScheduleByWorkPlanId(workPlanId);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT,result);
        } catch (Exception e) {
            log.error("查询指定医生出诊计划出错，form:{}", form, e);
            return CommonResult.error("回显失败！");
        }
    }

    @PostMapping("/updateSchedule")
    @Operation(summary = "修改指定医生出诊计划")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR_WORK_PLAN_SCHEDULE:UPDATE"}, mode = SaMode.OR)
    public CommonResult updateSchedule(@RequestBody @Valid UpdateDoctorScheduleForm form){
        try {
            Map<String, Object> map = BeanUtil.beanToMap(form);
            doctorWorkPlanScheduleService.updateSchedule(map);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("修改指定医生出诊计划出错，form:{}", form, e);
            return CommonResult.error("修改失败！");
        }
    }

    @PostMapping("/deleteWorkPlan")
    @Operation(summary = "删除指定医生出诊计划")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR_WORK_PLAN_SCHEDULE:DELETE"}, mode = SaMode.OR)
    public CommonResult deleteWorkPlan(@RequestBody @Valid DeleteWorkPlanForm form){
        try {
            Integer workPlanId = form.getWorkPlanId();
            doctorWorkPlanScheduleService.deleteWorkPlan(workPlanId);
            return CommonResult.ok();
        } catch (Exception e) {
            log.error("删除指定医生出诊计划出错，form:{}", form, e);
            return CommonResult.error("删除失败！");
        }
    }
}
