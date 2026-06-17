package com.hospital.hms.satoken;

import cn.dev33.satoken.SaManager;
import cn.dev33.satoken.stp.StpLogic;

/**
 * 患者端独立认证工具类
 * 与管理端StpUtil隔离，使用独立的token名称和存储空间
 */
public class StpPatientUtil {

    // 患者端登录类型标识，与管理端隔离
    public static final String TYPE = "patient";

    // 患者端独立的StpLogic实例
    public static StpLogic stpLogic = new StpLogic(TYPE);

    private StpPatientUtil() {
    }

    /**
     * 获取当前StpLogic实例
     */
    public static StpLogic getStpLogic() {
        return stpLogic;
    }

    /**
     * 登录
     */
    public static void login(Object id) {
        stpLogic.login(id);
    }

    /**
     * 登出
     */
    public static void logout() {
        stpLogic.logout();
    }

    /**
     * 获取token名称
     */
    public static String getTokenName() {
        return stpLogic.getTokenName();
    }

    /**
     * 获取token值
     */
    public static String getTokenValue() {
        return stpLogic.getTokenValue();
    }

    /**
     * 是否已登录
     */
    public static boolean isLogin() {
        return stpLogic.isLogin();
    }

    /**
     * 获取登录id（转为int）
     */
    public static int getLoginIdAsInt() {
        return stpLogic.getLoginIdAsInt();
    }

    /**
     * 获取登录id
     */
    public static Object getLoginId() {
        return stpLogic.getLoginId();
    }

    /**
     * 初始化StpLogic，注册到SaManager
     */
    public static void init() {
        SaManager.putStpLogic(stpLogic);
    }
}
