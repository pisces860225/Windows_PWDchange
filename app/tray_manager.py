import os
import sys
import pystray
import threading
import webbrowser
from PIL import Image, ImageDraw

from app.logger import get_logger

# 獲取日誌記錄器
logger = get_logger()


class TrayManager:
    """系統托盤管理器類，提供系統托盤圖標和選單功能"""

    def __init__(self, server_url="http://localhost:18080", shutdown_callback=None):
        """
        初始化系統托盤管理器

        :param server_url: 應用服務器URL
        :param shutdown_callback: 關閉應用的回調函數
        """
        self.server_url = server_url
        self.shutdown_callback = shutdown_callback
        self.tray_icon = None
        self.tray_thread = None
        logger.info("系統托盤管理器初始化")

    def _create_icon(self):
        """
        創建托盤圖標圖像

        :return: PIL 圖像對象
        """
        # 檢查是否有現成的圖標文件
        icon_path = self._get_icon_path()
        if icon_path and os.path.exists(icon_path):
            try:
                logger.debug(f"嘗試從文件加載圖標: {icon_path}")
                return Image.open(icon_path)
            except Exception as e:
                logger.warning(f"無法加載圖標文件: {e}")

        # 創建一個簡單的圖標
        logger.debug("創建默認圖標")
        image = Image.new("RGB", (64, 64), color=(0, 123, 255))
        dc = ImageDraw.Draw(image)

        # 繪製一個鎖的圖案
        dc.rectangle((20, 32, 44, 56), fill=(255, 255, 255))
        dc.rectangle((16, 20, 48, 32), fill=(0, 123, 255))
        dc.ellipse((20, 14, 44, 36), outline=(255, 255, 255), width=4)

        return image

    def _get_icon_path(self):
        """
        獲取圖標文件路徑

        :return: 圖標文件路徑
        """
        # 按優先順序查找這些可能的圖標文件
        icon_names = ["favicon.ico", "icon.ico", "app_icon.ico", "app.ico"]

        # 確定基礎目錄
        base_dir = self._get_application_path()

        # 查找圖標
        for name in icon_names:
            path = os.path.join(base_dir, name)
            if os.path.exists(path):
                return path

        return None

    def _get_application_path(self):
        """
        獲取應用程式目錄

        :return: 應用程式目錄路徑
        """
        # 如果是打包後的執行檔
        if getattr(sys, "frozen", False):
            return os.path.dirname(os.path.abspath(sys.executable))
        # 如果是直接執行的 Python 程式
        return os.path.dirname(os.path.abspath(__file__))

    def _open_browser(self, icon, item):
        """
        在瀏覽器中打開應用

        :param icon: 托盤圖標對象
        :param item: 菜單項對象
        """
        logger.info(f"打開瀏覽器訪問應用: {self.server_url}")
        try:
            webbrowser.open(self.server_url)
        except Exception as e:
            logger.error(f"打開瀏覽器失敗: {e}")

    def _exit_application(self, icon, item):
        """
        退出應用程式

        :param icon: 托盤圖標對象
        :param item: 菜單項對象
        """
        logger.info("從系統托盤收到退出命令")
        icon.stop()
        if self.shutdown_callback:
            logger.info("執行關閉回調函數")
            self.shutdown_callback()

    def _show_logs(self, icon, item):
        """
        打開日誌文件夾

        :param icon: 托盤圖標對象
        :param item: 菜單項對象
        """
        logger.info("嘗試打開日誌文件夾")
        try:
            # 獲取日誌文件夾路徑
            app_dir = self._get_application_path()
            log_dir = os.path.join(app_dir, "logs")

            # 確保目錄存在
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            # 在 Windows 上使用 explorer 打開文件夾
            os.system(f'explorer "{log_dir}"')
            logger.info(f"已打開日誌文件夾: {log_dir}")
        except Exception as e:
            logger.error(f"打開日誌文件夾失敗: {e}")

    def create_tray_icon(self):
        """
        創建並配置系統托盤圖標
        """
        logger.info("創建系統托盤圖標")
        icon_image = self._create_icon()

        # 創建托盤圖標和菜單
        self.tray_icon = pystray.Icon(
            "password_changer",
            icon_image,
            "Windows 密碼修改工具",
            menu=pystray.Menu(
                pystray.MenuItem("開啟應用", self._open_browser),
                pystray.MenuItem("查看日誌", self._show_logs),
                pystray.MenuItem("退出", self._exit_application),
            ),
        )
        logger.info("系統托盤圖標創建完成")

    def run_in_thread(self):
        """
        在獨立線程中運行托盤圖標
        """
        logger.info("啟動系統托盤線程")
        self.create_tray_icon()

        def run_tray():
            logger.info("系統托盤圖標開始運行")
            self.tray_icon.run()
            logger.info("系統托盤圖標已停止")

        self.tray_thread = threading.Thread(target=run_tray, daemon=True)
        self.tray_thread.start()
        logger.info("系統托盤線程已啟動")

        return self.tray_thread

    def stop(self):
        """
        停止托盤圖標
        """
        if self.tray_icon:
            logger.info("停止系統托盤圖標")
            self.tray_icon.stop()
