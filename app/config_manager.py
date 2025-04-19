import os
import sys
import json
from typing import Any, Dict
from app.logger import get_logger

# 獲取日誌記錄器
logger = get_logger()


class ConfigManager:
    """配置管理器類，管理應用程式配置"""

    # 默認配置
    DEFAULT_CONFIG = {
        "server": {
            "host": "0.0.0.0",
            "port": 18080,
            "auto_open_browser": True,
        },
        "logging": {
            "level": "INFO",
            "max_file_size_mb": 10,
            "backup_count": 5,
        },
        "tray": {
            "enabled": True,
            "minimize_to_tray": True,
            "close_to_tray": True,
        },
        "app": {
            "title": "Windows 使用者密碼修改工具",
            "locale": "zh-TW",
        },
        "security": {
            "enable_password_masking": True,
            "log_user_actions": True,
        },
    }

    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理器

        :param config_file: 配置文件路徑
        """
        self.config_file = self._get_config_path(config_file)
        logger.debug(f"使用配置文件: {self.config_file}")
        self.config = self._load_config()

    def _get_config_path(self, config_file: str) -> str:
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
                logger.debug(f"找到配置文件: {path}")
                return path

        # 如果找不到存在的配置文件，使用第一個路徑作為默認創建位置
        logger.debug(f"配置文件不存在，將創建於: {possible_paths[0]}")
        return possible_paths[0]

    def _load_config(self) -> Dict[str, Any]:
        """
        載入配置文件，如果不存在則創建默認配置

        :return: 配置字典
        """
        # 如果配置文件存在，載入它
        if os.path.exists(self.config_file):
            try:
                logger.info(f"正在載入配置文件: {self.config_file}")
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info("配置文件載入成功")

                # 確保配置結構完整，用默認值填補缺失的配置
                merged_config = self._merge_configs(self.DEFAULT_CONFIG, config)

                # 如果合併後的配置與原配置不同，保存更新後的配置
                if merged_config != config:
                    logger.info("配置結構已更新，保存更新後的配置")
                    self._save_config(merged_config)

                return merged_config

            except Exception as e:
                logger.error(f"載入配置文件失敗: {e}")
                logger.warning("將使用默認配置並創建新的配置文件")
        else:
            logger.info(f"配置文件不存在，創建默認配置: {self.config_file}")

        # 保存默認配置到文件
        self._save_config(self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG

    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        保存配置到文件

        :param config: 配置字典
        """
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logger.info(f"配置已保存到: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失敗: {e}")

    def _merge_configs(
        self, default: Dict[str, Any], user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        合併默認配置和用戶配置，確保所有必要的配置項都存在

        :param default: 默認配置
        :param user: 用戶配置
        :return: 合併後的配置
        """
        result = default.copy()

        # 遞迴合併字典
        def merge_dict(default_dict, user_dict):
            merged = default_dict.copy()
            for key, value in user_dict.items():
                if (
                    key in merged
                    and isinstance(merged[key], dict)
                    and isinstance(value, dict)
                ):
                    merged[key] = merge_dict(merged[key], value)
                else:
                    merged[key] = value
            return merged

        return merge_dict(default, user)

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        獲取配置值

        :param section: 配置區段
        :param key: 配置項名稱
        :param default: 默認值（如果配置不存在）
        :return: 配置值
        """
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception as e:
            logger.error(f"獲取配置 {section}.{key} 失敗: {e}")
            return default

    def set(self, section: str, key: str, value: Any) -> None:
        """
        設置配置值並保存到文件

        :param section: 配置區段
        :param key: 配置項名稱
        :param value: 新的配置值
        """
        if section not in self.config:
            self.config[section] = {}

        # 檢查值是否變更
        if (
            section in self.config
            and key in self.config[section]
            and self.config[section][key] == value
        ):
            logger.debug(f"配置 {section}.{key} 未變更")
            return

        # 更新配置並保存到文件
        self.config[section][key] = value
        logger.info(f"配置已更新: {section}.{key} = {value}")
        self._save_config(self.config)

    def get_all(self) -> Dict[str, Any]:
        """
        獲取所有配置

        :return: 所有配置的複本
        """
        return self.config.copy()

    def reset_to_default(self) -> None:
        """
        重置配置為默認值
        """
        logger.info("重置所有配置為默認值")
        self.config = self.DEFAULT_CONFIG.copy()
        self._save_config(self.config)

    def reset_section(self, section: str) -> None:
        """
        重置指定區段的配置為默認值

        :param section: 配置區段名稱
        """
        if section in self.DEFAULT_CONFIG:
            logger.info(f"重置配置區段 {section} 為默認值")
            self.config[section] = self.DEFAULT_CONFIG[section].copy()
            self._save_config(self.config)
        else:
            logger.warning(f"配置區段 {section} 不存在於默認配置中")


# 創建全局配置管理器實例
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """
    獲取配置管理器實例

    :return: 配置管理器
    """
    return config_manager
