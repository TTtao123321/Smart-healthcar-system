package com.hospital.hms.service.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.map.MapUtil;
import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONException;
import cn.hutool.json.JSONUtil;
import com.hospital.common.exception.GlobalException;
import com.hospital.common.utils.PageUtils;
import com.hospital.hms.dao.DeptSubDoctorDao;
import com.hospital.hms.dao.DoctorDao;
import com.hospital.hms.pojo.Doctor;
import com.hospital.hms.pojo.MedicalDeptSubDoctor;
import com.hospital.hms.service.DoctorService;
import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import io.minio.errors.*;
import lombok.extern.log4j.Log4j2;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.util.*;

@Log4j2
@Service
public class DoctorServiceImpl implements DoctorService {
    @Autowired
    private DoctorDao doctorDao;

    @Autowired
    private DeptSubDoctorDao deptSubDoctorDao;

    @Override
    public PageUtils selectConditionByPage(Map<String, Object> map) {
        int page = MapUtil.getInt(map, "page", 1);
        int length = MapUtil.getInt(map, "length", 10);
        Long totalCount = doctorDao.selectConditionByPageCount(map);
        if (totalCount == 0) {
            return new PageUtils(Collections.emptyList(), totalCount, page, length);
        }
        int startId = (page - 1) * length;
        map.put("start",startId);
        List<HashMap<String,Object>> list = doctorDao.selectConditionByPage(map);
        return new PageUtils(list,totalCount,page, length);
    }

    @Override
    @Transactional
    public void insert(Map<String, Object> map) {
        Doctor doctor = BeanUtil.toBean(map, Doctor.class);
        doctorDao.insert(doctor);
        Integer doctorId = doctor.getId();
        Integer subId = MapUtil.getInt(map, "subId");
        MedicalDeptSubDoctor medicalDeptSubDoctor = new MedicalDeptSubDoctor();
        medicalDeptSubDoctor.setDoctorId(doctorId);
        medicalDeptSubDoctor.setDeptSubId(subId);
        deptSubDoctorDao.insert(medicalDeptSubDoctor);
    }

    @Override
    public HashMap selectById(Integer id) {
        HashMap result = doctorDao.selectById(id);
        if (result != null && result.containsKey("tag")) {
            String tag = (String) result.get("tag");
            if (tag != null && !tag.isEmpty()) {
                try {
                    JSONArray array = JSONUtil.parseArray(tag);
                    result.put("tag", array);
                } catch (JSONException e) {
                    log.error("Error parsing tag JSON: ", e);
                }
            }
        }
        return result;
    }

    @Override
    @Transactional
    public void update(Map<String, Object> param) {
        doctorDao.update(param);
        Map<String, Object> map = MapUtil.renameKey(param, "id", "doctorId");
        deptSubDoctorDao.update(map);
    }

    @Override
    @Transactional
    public void deleteDoctorByIds(Integer[] ids) {
        doctorDao.deleteByIds(ids);
        deptSubDoctorDao.deleteByIds(ids);
    }

    @Override
    public HashMap selectDoctorDetailById(Integer id) {
        HashMap map = doctorDao.selectDoctorDetailById(id);
        JSONArray tag = JSONUtil.parseArray(map.get("tag"));
        map.put("tag", tag);
        return map;
    }

    @Value("${minio.endpoint}")
    private String endpoint;
    @Value("${minio.access-key}")
    private String accessKey;
    @Value("${minio.secret-key}")
    private String secretKey;
    @Value("${minio.bucket-name}")
    private String bucketName;

    private static final String DOCTOR_FILE_PREFIX = "doctor-";
    private static final String FILE_EXTENSION = ".jpg";
    private static final int MAX_FILE_SIZE = 5 * 1024 * 1024;

    @Override
    @Transactional
    public void updatePhoto(MultipartFile file, Integer doctorId) {
        String filename = DOCTOR_FILE_PREFIX + doctorId + FILE_EXTENSION;
        try {
            MinioClient minioClient = MinioClient.builder()
                    .endpoint(endpoint)
                    .credentials(accessKey, secretKey)
                    .build();
            minioClient.putObject(
                    PutObjectArgs.builder()
                            .bucket(bucketName)
                            .object("doctor/" + filename)
                            .stream(file.getInputStream(), -1, MAX_FILE_SIZE)
                            .contentType("image/jpeg")
                            .build()
            );
        } catch (Exception e) {
            log.error("头像上传至minio失败！");
            throw new GlobalException("修改头像出错！");
        }
        HashMap<String, Object> updateParams = new HashMap<>();
        updateParams.put("id", doctorId);
        updateParams.put("photo", "/doctor/" + filename);
        doctorDao.updatePicture(updateParams);
    }

    @Override
    public ArrayList<HashMap> selectDoctorsBySubId(Integer deptSubId) {
        return doctorDao.selectDoctorsBySubId(deptSubId);
    }

    @Override
    public ArrayList<HashMap> selectAllDoctorNameAndId() {
        return doctorDao.selectAllDoctorNameAndId();
    }
}
