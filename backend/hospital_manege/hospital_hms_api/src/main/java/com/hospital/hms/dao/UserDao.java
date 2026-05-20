package com.hospital.hms.dao;

import org.springframework.stereotype.Repository;

import java.util.Map;
import java.util.Set;

@Repository
public interface UserDao {
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
    Set<String> selectUserPrivileges(int userId);

    /**
     *
     * @param map
     * @return
     */
    Integer updatePassword(Map<String, Object> map);
}
