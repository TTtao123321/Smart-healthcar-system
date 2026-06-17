package com.hospital.hms.service;

import com.hospital.hms.pojo.Permission;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public interface PermissionService {
    List<Permission> selectAllPermissions();
}
