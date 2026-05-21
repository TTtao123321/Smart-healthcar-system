package com.hospital.hms.service.impl;

import cn.hutool.core.map.MapUtil;
import com.hospital.common.exception.GlobalException;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.common.OperationMessage;
import com.hospital.hms.dao.DeptSubDao;
import com.hospital.hms.pojo.MedicalDeptSub;
import com.hospital.hms.service.DeptSubService;
import lombok.extern.log4j.Log4j2;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;

@Log4j2
@Service
public class DeptSubServiceImpl implements DeptSubService {
    @Autowired
    private DeptSubDao deptSubDao;

    @Override
    public PageUtils selectConditionByPage(HashMap map) {
        Long totalCount = deptSubDao.selectConditionByPageCount(map);
        if (totalCount == 0) {
            return new PageUtils(Collections.emptyList(), totalCount,
                    MapUtil.getInt(map, "page"),
                    MapUtil.getInt(map, "length"));
        }
        Long pageIndex = MapUtil.getLong(map,"page");
        Long pageSize = MapUtil.getLong(map,"length");
        Long startId = (pageIndex - 1) * pageSize;
        map.put("start",startId);
        List<HashMap<String,Object>> list = deptSubDao.selectConditionByPage(map);
        return new PageUtils(list,totalCount,MapUtil.getInt(map, "page"), MapUtil.getInt(map, "length"));
    }

    @Override
    @Transactional
    public void insert(MedicalDeptSub deptSub) {
        deptSubDao.insert(deptSub);
    }

    @Override
    public HashMap selectById(Integer id) {
        return deptSubDao.selectById(id);
    }

    @Override
    @Transactional
    public void update(MedicalDeptSub deptSub) {
        deptSubDao.update(deptSub);
    }

    @Override
    @Transactional
    public void deleteByIds(Integer[] ids) {
        long count = deptSubDao.selectDoctorCountByIds(ids);
        if (count==0) {
            deptSubDao.deleteByIds(ids);
        }else{
            log.error("科室下有关联诊室，不可删除！");
            throw new GlobalException(OperationMessage.DOCTOR_EXISTS.toString());
        }
    }

    @Override
    public ArrayList<HashMap> selectSubByDeptId(Integer deptId) {
        return deptSubDao.selectSubByDeptId(deptId);
    }
}
