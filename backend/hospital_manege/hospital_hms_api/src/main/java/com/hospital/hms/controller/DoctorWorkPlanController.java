package com.hospital.hms.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import cn.dev33.satoken.annotation.SaCheckPermission;
import cn.dev33.satoken.annotation.SaMode;
import cn.hutool.core.bean.BeanUtil;
import com.hospital.hms.common.CommonResult;
import com.hospital.hms.common.OperationMessage;
import com.hospital.hms.controller.form.InsertWorkPlanForm;
import com.hospital.hms.controller.form.SelectDoctorWorkPlanInTime;
import com.hospital.hms.service.DoctorWorkPlanService;
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
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/doctor/work/plan")
@Tag(name = "DoctorWorkPlanController", description = "门诊日程管理")
@Slf4j
public class DoctorWorkPlanController {
    @Autowired
    private DoctorWorkPlanService doctorWorkPlanService;

    @PostMapping("/selectWorkPlanByTime")
    @Operation(summary = "按日期查询门诊日程")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR_WORK_PLAN:SELECT"}, mode = SaMode.OR)
    public CommonResult selectWorkPlanByTime(@RequestBody @Valid SelectDoctorWorkPlanInTime form){
        try {
            Map<String, Object> map = BeanUtil.beanToMap(form);
            ArrayList<String> dateList = doctorWorkPlanService.getDateList(form.getStartDate(),form.getEndDate(),false);
            Collection<HashMap> result = doctorWorkPlanService.selectWorkPlanByTime(map,dateList);
            ArrayList<String> resultDateList = doctorWorkPlanService.getDateList(form.getStartDate(),form.getEndDate(),true);
            return CommonResult.ok().put(CommonResult.RETURN_RESULT,result).put("dateList",resultDateList);
        } catch (Exception e) {
            log.error("查询门诊日程失败,form:{}", form, e);
            return CommonResult.error("查询失败！");
        }
    }

    @PostMapping("/insert")
    @Operation(summary = "添加门诊日程")
    @SaCheckLogin
    @SaCheckPermission(value = {"ROOT", "DOCTOR_WORK_PLAN:INSERT"}, mode = SaMode.OR)
    public CommonResult insert(@RequestBody @Valid InsertWorkPlanForm form){
        Map<String, Object> map = BeanUtil.beanToMap(form);
        String message = doctorWorkPlanService.insert(map);
        if (message == OperationMessage.PLAN_SAVE_OK.toString()) {
            return CommonResult.ok().put(CommonResult.RETURN_RESULT,"添加成功");
        }
        return CommonResult.error("添加失败！");
    }


}
