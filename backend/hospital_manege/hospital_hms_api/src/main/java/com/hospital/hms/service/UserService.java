package com.hospital.hms.service;

import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@Service
public interface UserService {
    /**
     *
     * @param map
     * @return
     */
    Integer login(Map<String, Object> map);

    /**
     *
     * @param userId
     * @return
     */
    ArrayList selectUserPermssions(Integer userId);

    /**
     *
     * @param map
     * @return
     */
    Integer updatePassword(Map<String, Object> map);

    HashMap selectUserByPage(Map<String, Object> map);

    HashMap selectUserById(Integer id);

    int insertUser(Map<String, Object> map);

    int updateUser(Map<String, Object> map);

    int deleteUserByIds(Integer[] ids);

    ArrayList selectUserRoleNames(Integer userId);
}
