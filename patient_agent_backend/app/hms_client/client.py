import logging
from typing import Any

import httpx

from app.config.settings import settings
from app.hms_client.exceptions import (
    HmsAuthError,
    HmsClientError,
    HmsNotFoundError,
    HmsServerError,
    HmsTimeoutError,
    HmsValidationError,
)
from app.hms_client.services.dept_service import DeptService
from app.hms_client.services.doctor_service import DoctorService
from app.hms_client.services.registration_service import RegistrationService

logger = logging.getLogger(__name__)


class HmsClient:
    """HMS REST-RPC 客户端"""

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self._base_url = base_url or settings.hms_api_url
        self._timeout = timeout or settings.hms_api_timeout
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
        )
        self._sa_token: str | None = None

        # 初始化服务
        self.dept_service = DeptService(self)
        self.doctor_service = DoctorService(self)
        self.registration_service = RegistrationService(self)

    async def login_admin(self, username: str = "admin", password: str = "") -> None:
        """使用管理员账号登录 HMS，获取 SaToken

        MVP 阶段使用默认管理员账号。生产环境应使用专用 API 账号。
        """
        if not password:
            password = settings.hms_admin_password

        try:
            response = await self._http.post(
                "/user/login",
                json={"username": username, "password": password},
            )
            data = response.json()
            token = data.get("token", "")
            if not token:
                token = data.get("result", {}).get("token", "")
            if token:
                self._sa_token = token
                self._http.headers["satoken"] = token
                logger.info("HMS 管理员登录成功")
            else:
                logger.warning(f"HMS 登录未获取到 token: {data}")
        except Exception as e:
            logger.error(f"HMS 管理员登录失败: {e}")
            # 不抛出异常，允许服务在无认证模式下启动（开发调试用）

    def set_token(self, token: str) -> None:
        """设置 SaToken 认证头"""
        self._sa_token = token
        self._http.headers["satoken"] = token

    def clear_token(self) -> None:
        """清除认证 token"""
        self._sa_token = None
        self._http.headers.pop("satoken", None)

    async def get(self, path: str, params: dict | None = None) -> Any:
        """发送 GET 请求"""
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict | None = None) -> Any:
        """发送 POST 请求"""
        return await self._request("POST", path, json=json)

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        """发送 HTTP 请求并处理响应"""
        try:
            response = await self._http.request(method, path, **kwargs)
        except httpx.TimeoutException as e:
            logger.error(f"HMS 请求超时: {method} {path}")
            raise HmsTimeoutError(f"请求超时: {path}") from e
        except httpx.RequestError as e:
            logger.error(f"HMS 请求失败: {method} {path}, error: {e}")
            raise HmsClientError(f"请求失败: {path}") from e

        # 处理响应状态码
        if response.status_code == 401:
            raise HmsAuthError("认证失败，请重新登录")
        if response.status_code == 404:
            raise HmsNotFoundError(f"资源不存在: {path}")
        if 400 <= response.status_code < 500:
            raise HmsValidationError(f"请求参数错误: {response.text}")
        if response.status_code >= 500:
            raise HmsServerError(
                f"HMS 服务端错误: {response.status_code}",
                status_code=response.status_code,
            )

        # 解析 HMS CommonResult 格式
        data = response.json()
        code = data.get("code", 200)
        if code != 200:
            msg = data.get("msg", "未知错误")
            if code == 401:
                raise HmsAuthError(msg)
            raise HmsClientError(f"HMS 返回错误: {msg}")

        return data

    async def close(self) -> None:
        """关闭客户端"""
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
