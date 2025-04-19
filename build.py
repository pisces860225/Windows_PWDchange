import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import logging
import json


# 設置打包過程的日誌記錄
def setup_build_logger():
    logger = logging.getLogger("build_process")
    logger.setLevel(logging.INFO)

    # 清除之前的處理器
    if logger.handlers:
        logger.handlers.clear()

    # 格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 創建日誌目錄
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_logs")
    os.makedirs(logs_dir, exist_ok=True)

    # 檔案處理器
    log_file = os.path.join(
        logs_dir, f'build_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'
    )
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 獲取日誌記錄器
logger = setup_build_logger()


# 創建默認配置文件
def create_default_config():
    config_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "config.json"
    )

    # 如果配置文件已經存在，不覆蓋它
    if os.path.exists(config_file):
        logger.info(f"配置文件已存在: {config_file}")
        return

    # 默認配置
    default_config = {
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

    # 寫入配置文件
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        logger.info(f"已創建默認配置文件: {config_file}")
    except Exception as e:
        logger.error(f"創建配置文件失敗: {e}")


def main():
    logger.info("開始打包 Windows 密碼修改工具...")

    # 確保靜態目錄存在
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)
    logger.info("已確認靜態資源目錄")

    # 確保模板目錄存在
    os.makedirs("templates", exist_ok=True)
    logger.info("已確認模板目錄")

    # 確保日誌目錄存在於打包後的環境中
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    logger.info(f"已確認日誌目錄: {logs_dir}")

    # 創建一個空的日誌文件，以便打包到執行檔中
    empty_log_file = os.path.join(logs_dir, ".keep")
    with open(empty_log_file, "w") as f:
        f.write("# 此目錄用於存放應用程式日誌\n")
    logger.info("已創建日誌佔位檔案")

    # 創建默認配置文件（如果不存在）
    create_default_config()
    logger.info("已確認配置文件")

    # 檢查相關的文件是否存在
    additional_files = {
        "sample_config.json": "範例配置文件",
        "config_instructions.txt": "配置說明文件",
        "troubleshooting.txt": "故障排除指南",
        "啟動密碼修改工具.bat": "啟動批處理文件",
    }

    missing_files = []
    for file_name, file_desc in additional_files.items():
        if not os.path.exists(file_name):
            missing_files.append(f"{file_name} ({file_desc})")
            logger.warning(f"未找到 {file_name}，將不包含此文件")

    if missing_files:
        logger.warning(f"以下文件缺失: {', '.join(missing_files)}")

    # 建立打包目錄
    build_dir = Path("build")
    dist_dir = Path("dist")

    if build_dir.exists():
        shutil.rmtree(build_dir)
        logger.info("已清除舊的build目錄")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        logger.info("已清除舊的dist目錄")

    # 準備要包含的數據文件
    include_data_files = [
        "--include-data-files=config.json=config.json",  # 包含配置文件
    ]

    # 添加存在的其他文件
    for file_name in additional_files:
        if os.path.exists(file_name):
            include_data_files.append(f"--include-data-files={file_name}={file_name}")
            logger.info(f"已添加文件: {file_name}")

    # 準備Nuitka命令
    cmd = (
        [
            sys.executable,
            "-m",
            "nuitka",
            "--standalone",  # 創建獨立的可執行文件
            # "--onefile",  # 打包為單一檔案 (注釋掉，改用多文件模式)
            "--windows-uac-admin",  # 啟用UAC管理員權限
            (
                "--windows-icon-from-ico=favicon.ico"
                if os.path.exists("favicon.ico")
                else ""
            ),
            "--include-data-dir=templates=templates",  # 包含模板目錄
            "--include-data-dir=static=static",  # 包含靜態資源目錄
            "--include-data-dir=logs=logs",  # 包含日誌目錄
        ]
        + include_data_files
        + [
            "--output-dir=dist",  # 輸出到dist目錄
            "--remove-output",  # 如果輸出已存在則移除
            "--windows-disable-console",  # 禁用控制台窗口
            "--windows-company-name=Windows密碼修改工具",
            "--windows-product-name=Windows密碼修改工具",
            "--windows-file-version=1.0.0.0",
            "--windows-product-version=1.0.0.0",
            "--windows-file-description=Windows密碼修改工具",
            "--enable-plugin=pyside6",  # 添加插件支援
            "--enable-plugin=tk-inter",  # 添加插件支援
            "--enable-plugin=pylint-warnings",  # 忽略pylint警告
            "--follow-imports",  # 跟隨導入
            "--include-package=pystray",  # 確保包含pystray包
            "--include-package=PIL",  # 確保包含PIL包
            "--include-module=webbrowser",  # 確保包含webbrowser模塊
            "--include-module=threading",  # 確保包含threading模塊
            "--include-module=signal",  # 確保包含signal模塊
            "--include-module=json",  # 確保包含json模塊
            "--include-module=socket",  # 確保包含socket模塊
            "--disable-console",  # 禁用控制台窗口
            "--show-memory",  # 顯示內存使用情況
            "--show-progress",  # 顯示打包進度
            "--plugin-enable=anti-bloat",  # 啟用抗膨脹插件
            "--static-libpython=no",  # 不使用靜態 Python 庫
            "--include-package-data=fastapi",  # 包含 fastapi 資源
            "--include-package-data=uvicorn",  # 包含 uvicorn 資源
            "--prefer-source-code",  # 優先使用源代碼
            "main.py",  # 主程式檔案
        ]
    )

    # 過濾空命令
    cmd = [item for item in cmd if item]

    # 執行打包命令
    logger.info(f"執行命令: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        logger.info("打包命令執行成功")
    except subprocess.CalledProcessError as e:
        logger.error(f"打包失敗：{e}")
        return 1

    # 為單一檔案模式，我們不需要創建批處理文件
    if os.path.exists("dist/main.exe"):
        # 重命名執行檔為更易於識別的名稱
        new_name = "Windows密碼修改工具.exe"
        try:
            os.rename("dist/main.exe", f"dist/{new_name}")
            logger.info(f"執行檔已重命名為: {new_name}")
        except Exception as e:
            logger.error(f"重命名失敗: {e}")

    # 複製啟動批處理文件到dist目錄
    if os.path.exists("啟動密碼修改工具.bat"):
        try:
            shutil.copy("啟動密碼修改工具.bat", "dist/")
            logger.info("已複製啟動批處理文件到dist目錄")
        except Exception as e:
            logger.error(f"複製啟動批處理文件失敗: {e}")

    # 執行打包後處理
    logger.info("執行打包後處理...")
    for action in post_build_actions:
        try:
            action()
        except Exception as e:
            logger.error(f"執行打包後處理時發生錯誤: {e}")

    logger.info("打包完成，您可以在 dist 目錄中找到單一執行檔。")
    logger.info(
        "日誌功能已啟用，應用程式運行時將自動在同目錄的logs文件夾中創建日誌文件。"
    )
    logger.info(
        "系統托盤功能已啟用，應用程式運行時將在系統托盤顯示圖標，可以通過右鍵菜單關閉應用。"
    )
    logger.info("配置功能已啟用，可通過編輯config.json文件自定義應用程式設置。")
    logger.info("故障排除功能已添加，若遇到問題請參考troubleshooting.txt文件。")
    logger.info("自動端口檢測已啟用，如果默認端口被佔用，將自動尋找可用端口。")

    # 顯示使用說明
    logger.info("")
    logger.info("=== 使用方法 ===")
    logger.info("1. 運行dist目錄中的「啟動密碼修改工具.bat」來啟動應用程式")
    logger.info("2. 或直接雙擊「Windows密碼修改工具.exe」(建議以管理員身份運行)")
    logger.info("3. 應用程式啟動後會自動在系統托盤顯示圖標")
    logger.info("4. 如果瀏覽器未自動打開，請右鍵點擊托盤圖標並選擇「開啟應用」")

    # 打包後複製檔案的處理
    def post_build_copy_config():
        """打包後複製配置文件到輸出目錄"""
        # 查找打包後的執行文件
        exe_path = None
        if os.path.exists("dist/main.exe"):
            exe_path = "dist/main.exe"
        elif os.path.exists("dist/Windows密碼修改工具.exe"):
            exe_path = "dist/Windows密碼修改工具.exe"

        if exe_path:
            # 複製配置文件到執行檔所在目錄
            shutil.copy("config.json", os.path.dirname(exe_path))
            logger.info(f"已複製配置文件到 {os.path.dirname(exe_path)}")

            # 確保日誌目錄存在
            log_dir = os.path.join(os.path.dirname(exe_path), "logs")
            os.makedirs(log_dir, exist_ok=True)
            logger.info(f"已創建日誌目錄 {log_dir}")

    # 註冊打包後的處理
    post_build_actions = [post_build_copy_config]

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        logger.info(f"打包過程結束，退出碼: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"打包過程發生異常: {str(e)}")
        logger.exception("打包過程中發生未預期的異常")
        sys.exit(1)
