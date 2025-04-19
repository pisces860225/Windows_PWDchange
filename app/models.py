from pydantic import BaseModel, Field, validator


class PasswordChange(BaseModel):
    username: str = Field(..., description="Windows 使用者名稱")
    current_password: str = Field(..., description="目前密碼")
    new_password: str = Field(..., description="新密碼")
    confirm_password: str = Field(..., description="確認新密碼")

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs) -> str:
        """
        驗證確認密碼是否與新密碼相同

        :param v: 確認密碼
        :param values: 其他字段值
        :param kwargs: 其他參數
        :return: 確認密碼
        """
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("確認密碼與新密碼不符")
        return v
