class HmsClientError(Exception):
    """HMS 客户端基础异常"""

    def __init__(self, message: str = "HMS 客户端错误"):
        self.message = message
        super().__init__(self.message)


class HmsTimeoutError(HmsClientError):
    """请求超时"""

    def __init__(self, message: str = "HMS 请求超时"):
        super().__init__(message)


class HmsNotFoundError(HmsClientError):
    """资源不存在（科室/医生/排班未找到）"""

    def __init__(self, message: str = "请求的资源不存在"):
        super().__init__(message)


class HmsServerError(HmsClientError):
    """HMS 服务端错误（5xx）"""

    def __init__(self, message: str = "HMS 服务端错误", status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class HmsAuthError(HmsClientError):
    """认证失败"""

    def __init__(self, message: str = "HMS 认证失败"):
        super().__init__(message)


class HmsValidationError(HmsClientError):
    """请求参数校验失败（4xx）"""

    def __init__(self, message: str = "请求参数校验失败"):
        super().__init__(message)
