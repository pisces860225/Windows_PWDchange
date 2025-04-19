import win32net
import win32api
import win32netcon
import win32security
from typing import Dict, Any

from app.logger import get_logger, Logger
from app.config_manager import get_config

# 獲取日誌記錄器
logger = get_logger()

# 獲取配置管理器
config = get_config()


class PasswordService:
    @staticmethod
    def change_password(
        username: str, current_password: str, new_password: str
    ) -> Dict[str, Any]:
        """
        修改 Windows 使用者的密碼

        Args:
            username: Windows 使用者名稱
            current_password: 目前密碼
            new_password: 新密碼

        Returns:
            包含操作結果的字典
        """
        # 檢查是否需要記錄用戶操作
        log_user_actions = config.get("security", "log_user_actions", True)
        # 檢查是否啟用密碼遮罩
        enable_password_masking = config.get(
            "security", "enable_password_masking", True
        )

        if log_user_actions:
            logger.info(f"嘗試修改用戶 '{username}' 的密碼")
            if enable_password_masking:
                safe_current_pwd = Logger.format_password_log(current_password)
                safe_new_pwd = Logger.format_password_log(new_password)
                logger.debug(
                    f"用戶: {username}, 當前密碼: {safe_current_pwd}, 新密碼: {safe_new_pwd}"
                )
        else:
            logger.info("嘗試修改用戶密碼")

        try:
            # 嘗試驗證目前使用者憑證
            domain = win32api.GetComputerName()
            logger.debug(f"使用電腦名稱作為域: {domain}")

            # 驗證目前密碼是否正確
            try:
                if log_user_actions:
                    logger.info(f"驗證用戶 '{username}' 的當前密碼")
                else:
                    logger.info("驗證當前密碼")
                hUser = win32security.LogonUser(
                    username,
                    domain,
                    current_password,
                    win32security.LOGON32_LOGON_NETWORK,
                    win32security.LOGON32_PROVIDER_DEFAULT,
                )
                hUser.Close()
                if log_user_actions:
                    logger.info(f"用戶 '{username}' 的當前密碼驗證成功")
                else:
                    logger.info("當前密碼驗證成功")
            except Exception as e:
                error_msg = f"密碼驗證失敗: {str(e)}"
                logger.error(error_msg)
                if log_user_actions:
                    logger.error(
                        f"用戶 '{username}' 的密碼驗證失敗: 密碼不正確或用戶不存在"
                    )
                else:
                    logger.error("密碼驗證失敗: 密碼不正確或用戶不存在")
                return {"success": False, "message": "目前密碼不正確或使用者不存在"}

            # 修改密碼
            if log_user_actions:
                logger.info(f"開始修改用戶 '{username}' 的密碼")
            else:
                logger.info("開始修改密碼")

            user_info = {
                "name": username,
                "password": new_password,
                "flags": win32netcon.UF_SCRIPT | win32netcon.UF_NORMAL_ACCOUNT,
            }
            win32net.NetUserSetInfo(None, username, 1003, user_info)
            success_msg = f"使用者 {username} 的密碼已成功修改"

            if log_user_actions:
                logger.info(success_msg)
            else:
                logger.info("密碼已成功修改")

            return {"success": True, "message": success_msg}

        except Exception as e:
            error_msg = f"無法修改密碼: {str(e)}"
            logger.error(error_msg)
            logger.exception("密碼修改過程中發生異常")
            return {"success": False, "message": error_msg}
