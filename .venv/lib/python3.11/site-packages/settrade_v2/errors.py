class SettradeError(Exception):
    def __init__(self, code: str, message: str, status_code: int, *args, **kwargs):
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class InvalidEnvironmentError(SettradeError):
    code = ""
    status_code = 0
    message = "Invalid environment ('prod', 'uat')"

    def __init__(self):
        super().__init__(
            message=self.message, code=self.code, status_code=self.status_code
        )
