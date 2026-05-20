package com.hospital.hms.service.impl;

import cn.hutool.core.map.MapUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.crypto.digest.MD5;
import com.hospital.hms.dao.UserDao;
import com.hospital.hms.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Map;
import java.util.Set;

@Service
public class UserServiceImpl implements UserService {

    public static final Integer PREFIX_LENGTH=6;

    public static final Integer SUFFIX_LENGTH=3;

    @Autowired
    private UserDao userDao;

    @Override
    public Integer login(Map<String, Object> map) {
        String username = MapUtil.getStr(map, "username");
        String password = MapUtil.getStr(map, "password");
        password = encryptPassword(username, password);
        map.put("password", password);
        return userDao.login(map);
    }

    private String encryptPassword(String username, String password) {
        // 创建MD5实例来进行加密
        MD5 md5 = MD5.create();
        // 使用MD5对用户名进行加密生成哈希字符串
        String temp = md5.digestHex(username);
        // 从MD5结果中提取出前缀部分（前6个字符）
        String tempStart = StrUtil.subWithLength(temp, 0, PREFIX_LENGTH);
        // 从MD5结果中提取出后缀部分（最后3个字符）
        String tempEnd = StrUtil.subSuf(temp, temp.length() - SUFFIX_LENGTH);
        // 将前缀、密码和后缀拼接起来，并对拼接结果进行MD5加密
        return md5.digestHex(tempStart + password + tempEnd);
    }

    @Override
    public ArrayList selectUserPermssions(Integer userId) {
        Set<String> permissions = userDao.selectUserPrivileges(userId);
        ArrayList list = new ArrayList();
        list.addAll(permissions);
        return list;
    }

    @Override
    @Transactional
    public Integer updatePassword(Map<String, Object> map) {
        //在数据库对明文密码进行加密
        return userDao.updatePassword(map);
    }
}
