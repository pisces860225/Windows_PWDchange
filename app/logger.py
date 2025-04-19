import os
import sys
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


class Logger:
    """日誌記錄器類，提供應用程式日誌記錄功能"""

    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_MAX_FILE_SIZE_MB = 10
    DEFAULT_BACKUP_COUNT = 5

    def __init__(self, log_level=None):
        """
        初始化日誌記錄器

        :param log_level: 日誌級別，預設為INFO
        """
        self.logger = logging.getLogger("password_change_app")
        self.config = self._load_config()

        # 設置日誌級別
        if log_level is None:
            # 從配置獲取日誌級別
            log_level_str = self.config.get("logging", {}).get("level", "INFO")
            log_level = self._get_log_level_from_str(log_level_str)

        self.logger.setLevel(log_level)
        self.log_folder = self._get_log_folder()
        self._setup_logger()

    def _get_log_level_from_str(self, level_str):
        """
        將字符串日誌級別轉換為logging級別常數

        :param level_str: 字符串日誌級別
        :return: logging級別常數
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(level_str.upper(), logging.INFO)

    def _load_config(self):
        """
        載入配置文件，如果不存在則返回空字典

        :return: 配置字典
        """
        # 獲取配置文件路徑
        config_path = self._get_config_path("config.json")

        # 如果配置文件存在，載入它
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                # 如果無法載入配置，使用默認值
                pass

        # 返回空字典
        return {}

    def _get_config_path(self, config_file):
        """
        獲取配置文件的完整路徑

        :param config_file: 配置文件名稱
        :return: 配置文件完整路徑
        """
        # 嘗試多個可能的路徑位置
        possible_paths = []

        # 確定應用程式根目錄
        if getattr(sys, "frozen", False):
            # 如果是打包後的執行檔 (PyInstaller 或 Nuitka)
            base_dir = os.path.dirname(os.path.abspath(sys.executable))
            possible_paths.append(os.path.join(base_dir, config_file))

            # Nuitka 打包後可能的其他路徑
            possible_paths.append(os.path.join(os.path.dirname(base_dir), config_file))
            possible_paths.append(config_file)  # 當前工作目錄
        else:
            # 如果是直接執行的 Python 程式
            base_dir = os.path.dirname(os.path.abspath(__file__))
            possible_paths.append(os.path.join(base_dir, config_file))
            possible_paths.append(config_file)  # 當前工作目錄

        # 嘗試找到存在的配置文件
        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 如果找不到存在的配置文件，使用第一個路徑作為默認路徑
        return possible_paths[0]

    def _get_log_folder(self):
        """
        獲取日誌文件夾路徑

        :return: 日誌文件夾路徑
        """
        possible_log_dirs = []

        # 如果是打包後的執行檔
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(os.path.abspath(sys.executable))
            possible_log_dirs.append(os.path.join(base_dir, "logs"))

            # Nuitka 打包後可能的其他路徑
            possible_log_dirs.append(os.path.join(os.path.dirname(base_dir), "logs"))
            possible_log_dirs.append("logs")  # 相對於當前工作目錄
        else:
            # 如果是直接執行的 Python 程式
            base_dir = os.path.dirname(os.path.abspath(__file__))
            possible_log_dirs.append(os.path.join(base_dir, "logs"))
            possible_log_dirs.append("logs")  # 相對於當前工作目錄

        # 使用第一個路徑作為日誌目錄
        log_dir = possible_log_dirs[0]

        # 確保目錄存在
        for dir_path in possible_log_dirs:
            os.makedirs(dir_path, exist_ok=True)

        # 嘗試寫入測試文件，確認目錄可寫
        for dir_path in possible_log_dirs:
            try:
                test_file = os.path.join(dir_path, ".test_write")
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                log_dir = dir_path
                break
            except (IOError, PermissionError):
                continue

        return log_dir

    def _setup_logger(self):
        """設置日誌格式和處理器"""
        # 清除之前的處理器
        if self.logger.handlers:
            self.logger.handlers.clear()

        # 格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 檔案處理器 - 每日日誌文件
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_folder, f"password_change_{today}.log")

        # 從配置獲取日誌文件大小和備份數量
        max_file_size_mb = self.config.get("logging", {}).get(
            "max_file_size_mb", self.DEFAULT_MAX_FILE_SIZE_MB
        )
        backup_count = self.config.get("logging", {}).get(
            "backup_count", self.DEFAULT_BACKUP_COUNT
        )

        # 使用 RotatingFileHandler 限制單個日誌文件大小
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,  # 轉換為字節
            backupCount=backup_count,  # 備份數量
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 記錄應用程式啟動
        self.logger.info("=" * 50)
        self.logger.info("應用程式啟動")
        self.logger.info(f"日誌存儲在: {self.log_folder}")
        self.logger.info(f"日誌級別: {logging.getLevelName(self.logger.level)}")
        self.logger.info(
            f"日誌文件大小限制: {max_file_size_mb}MB，保留 {backup_count} 個備份"
        )

    def get_logger(self):
        """
        獲取日誌記錄器實例

        :return: 日誌記錄器
        """
        return self.logger

    @staticmethod
    def format_password_log(password):
        """
        格式化密碼以便安全地記錄

        :param password: 原密碼
        :return: 格式化後的密碼字符串
        """
        if not password:
            return "空密碼"

        # 只顯示密碼長度和前兩個字符（如果有）
        masked = (
            password[:2] + "*" * (len(password) - 2)
            if len(password) > 2
            else "*" * len(password)
        )
        return f"{masked} (長度: {len(password)})"


# 創建全局日誌記錄器實例
app_logger = Logger().get_logger()


def get_logger():
    """
    獲取應用程式日誌記錄器

    :return: 日誌記錄器
    """
    return app_logger
