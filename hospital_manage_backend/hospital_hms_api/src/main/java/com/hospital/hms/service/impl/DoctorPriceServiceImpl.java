package com.hospital.hms.service.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.map.MapUtil;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.dao.DoctorPriceDao;
import com.hospital.hms.pojo.DoctorPrice;
import com.hospital.hms.service.DoctorPriceService;
import lombok.extern.log4j.Log4j2;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Log4j2
@Service
public class DoctorPriceServiceImpl implements DoctorPriceService {

    @Autowired
    private DoctorPriceDao doctorPriceDao;

    @Override
    public PageUtils selectByPage(Map<String, Object> map) {
        int page = MapUtil.getInt(map, "page", 1);
        int length = MapUtil.getInt(map, "length", 10);
        Long totalCount = doctorPriceDao.selectByPageCount(map);
        if (totalCount == 0) {
            return new PageUtils(Collections.emptyList(), totalCount, page, length);
        }
        int startId = (page - 1) * length;
        map.put("start", startId);
        List<HashMap<String, Object>> list = doctorPriceDao.selectByPage(map);
        return new PageUtils(list, totalCount, page, length);
    }

    @Override
    @Transactional
    public void insert(Map<String, Object> map) {
        DoctorPrice doctorPrice = BeanUtil.toBean(map, DoctorPrice.class);
        doctorPriceDao.insert(doctorPrice);
    }

    @Override
    @Transactional
    public void update(Map<String, Object> param) {
        doctorPriceDao.update(param);
    }

    @Override
    @Transactional
    public void deleteByIds(Integer[] ids) {
        doctorPriceDao.deleteByIds(ids);
    }
}
