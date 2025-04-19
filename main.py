import os
import sys
import time
import signal
import socket
import uvicorn
import threading
import webbrowser
from typing import Optional, Tuple
from pydantic import ValidationError
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models import PasswordChange
from app.services import PasswordService
from app.logger import get_logger
from app.tray_manager import TrayManager
from app.config_manager import get_config


# 設置工作目錄為執行檔所在目錄 (解決 Nuitka 打包後的路徑問題)
if getattr(sys, "frozen", False):
    # 如果是打包後的可執行文件
    application_path = os.path.dirname(os.path.abspath(sys.executable))
    # 將當前工作目錄更改為應用程式目錄
    os.chdir(application_path)
    print(f"已將工作目錄設置為: {application_path}")

    # 將可執行文件目錄添加到 sys.path
    if application_path not in sys.path:
        sys.path.insert(0, application_path)
        print(f"已將 {application_path} 添加到 sys.path")

# 獲取日誌記錄器
logger = get_logger()

# 獲取配置管理器
config = get_config()

# 定義伺服器停止事件和變數
stop_event = threading.Event()
server_thread = None
server_instance = None
tray_manager = None


# 獲取應用程式目錄
def get_application_path() -> str:
    """
    獲取應用程式目錄

    :return: 應用程式目錄路徑
    """
    # 如果是打包後的執行檔
    if getattr(sys, "frozen", False):
        # 獲取執行文件所在目錄
        exec_dir = os.path.dirname(os.path.abspath(sys.executable))

        # 檢查 Nuitka 打包目錄結構
        if os.path.basename(exec_dir).endswith(".dist"):
            # 這可能是 Nuitka 的 .dist 目錄
            app_dir = exec_dir
        elif os.path.exists(os.path.join(exec_dir, "main.dist")):
            # 主目錄下有 main.dist 子目錄
            app_dir = os.path.join(exec_dir, "main.dist")
        else:
            # 使用執行文件所在目錄
            app_dir = exec_dir

        # 檢查目錄是否存在必要的子目錄
        for required_dir in ["templates", "static"]:
            if not os.path.exists(os.path.join(app_dir, required_dir)):
                for parent_dir in [exec_dir, os.path.dirname(exec_dir)]:
                    if os.path.exists(os.path.join(parent_dir, required_dir)):
                        app_dir = parent_dir
                        break
    else:
        # 如果是直接執行的 Python 程式
        app_dir = os.path.dirname(os.path.abspath(__file__))

    # 將應用目錄添加到系統路徑
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    return app_dir


# 應用程式目錄
app_dir = get_application_path()
logger.info(f"應用程式目錄: {app_dir}")

# 創建 FastAPI 應用
app_title = config.get("app", "title", "Windows 使用者密碼修改工具")
app = FastAPI(title=app_title)
logger.info(f"FastAPI 應用已創建, 標題: {app_title}")

# 設置靜態文件目錄和模板目錄
static_dir = os.path.join(app_dir, "static")
templates_dir = os.path.join(app_dir, "templates")
logger.debug(f"靜態目錄: {static_dir}")
logger.debug(f"模板目錄: {templates_dir}")

# 確保目錄存在
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# 設置靜態文件目錄
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 設置模板目錄
templates = Jinja2Templates(directory=templates_dir)


# 首頁路由
@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request, message: Optional[str] = None, success: Optional[bool] = None
) -> HTMLResponse:
    """
    首頁路由

    :param request: FastAPI 請求對象
    :param message: 訊息
    :param success: 成功與否
    :return: HTMLResponse
    """
    logger.info("訪問首頁")
    if message:
        log_level = logger.info if success else logger.warning
        log_level(f"顯示訊息 - {'成功' if success else '失敗'}: {message}")

    return templates.TemplateResponse(
        "index.html", {"request": request, "message": message, "success": success}
    )


# 密碼修改處理路由
@app.post("/change-password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    username: str = Form(...),
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
) -> HTMLResponse:
    """
    密碼修改處理路由

    :param request: FastAPI 請求對象
    :param username: 使用者名稱
    :param current_password: 目前密碼
    :param new_password: 新密碼
    :param confirm_password: 確認新密碼
    :return: HTMLResponse
    """
    # 檢查是否需要記錄用戶操作
    log_user_actions = config.get("security", "log_user_actions", True)

    if log_user_actions:
        logger.info(f"接收到用戶 '{username}' 的密碼修改請求")
    else:
        logger.info(f"接收到密碼修改請求")

    try:
        # 使用模型驗證數據
        logger.debug("驗證表單數據")
        password_data = PasswordChange(
            username=username,
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password,
        )

        if log_user_actions:
            logger.info(f"用戶 '{username}' 的表單數據驗證成功")
        else:
            logger.info("表單數據驗證成功")

        # 執行密碼修改
        if log_user_actions:
            logger.info(f"開始執行用戶 '{username}' 的密碼修改")
        else:
            logger.info("開始執行密碼修改操作")

        result = PasswordService.change_password(
            username=password_data.username,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )

        # 返回結果頁面
        if result["success"]:
            if log_user_actions:
                logger.info(f"用戶 '{username}' 的密碼修改成功")
            else:
                logger.info("密碼修改操作成功")
        else:
            if log_user_actions:
                logger.warning(f"用戶 '{username}' 的密碼修改失敗: {result['message']}")
            else:
                logger.warning(f"密碼修改操作失敗: {result['message']}")

        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "success": result["success"],
                "message": result["message"],
            },
        )

    except ValidationError as e:
        # 處理驗證錯誤
        errors = e.errors()
        error_message = errors[0]["msg"] if errors else "輸入數據驗證失敗"
        logger.error(f"表單驗證錯誤: {error_message}")
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "message": error_message, "success": False},
        )
    except Exception as e:
        # 處理其他異常
        error_message = f"發生錯誤: {str(e)}"
        logger.error(error_message)
        logger.exception("處理密碼修改請求時發生未預期的異常")
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "message": error_message, "success": False},
        )


# API路由：獲取所有配置
@app.get("/api/config")
async def get_all_config(request: Request):
    """
    獲取所有配置
    """
    logger.info("通過API獲取所有配置")
    return config.get_all()


# API路由：更新配置
@app.post("/api/config/{section}/{key}")
async def update_config(request: Request, section: str, key: str, value: str):
    """
    更新配置
    """
    # 嘗試將值轉換為適當的類型
    try:
        # 檢查值是否為布爾型
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        # 檢查值是否為數字
        elif value.isdigit():
            value = int(value)
        elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
            value = float(value)
    except:
        pass

    logger.info(f"通過API更新配置: {section}.{key} = {value}")
    config.set(section, key, value)
    return {"success": True, "message": f"已更新配置 {section}.{key}"}


# API路由：重置配置
@app.post("/api/config/reset")
async def reset_config(request: Request, section: Optional[str] = None):
    """
    重置配置
    """
    if section:
        logger.info(f"通過API重置配置區段: {section}")
        config.reset_section(section)
        return {"success": True, "message": f"已重置配置區段 {section}"}
    else:
        logger.info("通過API重置所有配置")
        config.reset_to_default()
        return {"success": True, "message": "已重置所有配置"}


# 檢查端口是否可用
def is_port_available(host: str, port: int) -> bool:
    """
    檢查指定的端口是否可用

    :param host: 主機地址
    :param port: 端口號
    :return: 端口是否可用
    """
    try:
        # 創建測試用 socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            # 嘗試綁定端口
            s.bind((host, port))
            return True
    except (socket.error, OSError):
        return False


# 尋找可用端口
def find_available_port(
    start_port: int, host: str = "0.0.0.0", max_attempts: int = 10
) -> int:
    """
    尋找可用的端口

    :param start_port: 起始端口號
    :param host: 主機地址
    :param max_attempts: 最大嘗試次數
    :return: 可用的端口號
    """
    port = start_port
    for _ in range(max_attempts):
        if is_port_available(host, port):
            return port
        port += 1

    # 如果找不到可用端口，返回 0
    return 0


# 關閉應用的函數
def shutdown_application():
    """
    關閉應用程式
    """
    global server_instance, stop_event

    logger.info("正在關閉應用程式...")

    # 觸發停止事件
    stop_event.set()

    # 如果服務器實例存在，關閉它
    if server_instance:
        logger.info("關閉伺服器")
        server_instance.should_exit = True
        server_instance.force_exit = True

    logger.info("應用程式關閉完成")


# 在獨立線程中運行伺服器
def run_server_in_thread(host=None, port=None, auto_find_port=True) -> Tuple[bool, int]:
    """
    在獨立線程中運行伺服器

    :param host: 伺服器主機地址
    :param port: 伺服器端口
    :param auto_find_port: 是否自動尋找可用端口
    :return: (是否成功啟動, 實際使用的端口)
    """
    global server_instance, server_thread, stop_event

    # 從配置獲取主機和端口（如果未提供）
    if host is None:
        host = config.get("server", "host", "0.0.0.0")

    if port is None:
        port = config.get("server", "port", 18080)

    # 檢查端口是否可用
    if not is_port_available(host, port):
        logger.warning(f"端口 {port} 已被佔用")

        if auto_find_port:
            # 尋找可用端口
            new_port = find_available_port(port + 1, host)
            if new_port > 0:
                logger.info(f"自動切換到可用端口: {new_port}")
                port = new_port
                # 更新配置
                config.set("server", "port", port)
            else:
                logger.error("無法找到可用端口，無法啟動伺服器")
                return False, 0
        else:
            logger.error(f"端口 {port} 已被佔用，而且未啟用自動端口查找")
            return False, 0

    # 創建事件標誌來指示伺服器是否成功啟動
    server_started = threading.Event()
    server_start_error = [None]  # 使用列表存儲錯誤，以便能夠在閉包中修改

    def run():
        global server_instance
        try:
            # 直接使用應用實例而不是字符串引用
            uvicorn_config = uvicorn.Config(
                app=app, host=host, port=port, log_level="info"
            )
            server_instance = uvicorn.Server(uvicorn_config)
            server_instance.install_signal_handlers = (
                lambda: None
            )  # 禁用 uvicorn 的信號處理

            # 標記伺服器已成功初始化
            server_started.set()

            # 運行伺服器
            logger.info(f"啟動伺服器於 {host}:{port}")
            server_instance.run()
        except Exception as e:
            logger.error(f"伺服器運行失敗: {str(e)}")
            logger.exception("伺服器運行異常詳情")
            server_start_error[0] = str(e)
            server_started.set()  # 設置事件以解除等待

    server_thread = threading.Thread(target=run, daemon=True)
    server_thread.start()

    # 等待伺服器啟動或出錯
    server_started.wait(timeout=10)  # 等待最多10秒

    # 檢查是否有啟動錯誤
    if server_start_error[0] is not None:
        logger.error(f"伺服器啟動失敗: {server_start_error[0]}")
        return False, 0

    # 給伺服器一點時間來完成初始化
    time.sleep(2)

    # 改進端口檢測邏輯：嘗試連接到服務器而不是檢查端口是否可用
    def check_server_running():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect(("localhost", port))
                return True
        except:
            return False

    # 確認伺服器是否正在運行
    server_running = check_server_running()
    if server_running:
        logger.info(f"伺服器成功啟動於 {host}:{port}")

        # 如果設置為自動開啟瀏覽器，則開啟
        if config.get("server", "auto_open_browser", True):
            try:
                url = f"http://localhost:{port}"
                logger.info(f"自動開啟瀏覽器訪問: {url}")
                webbrowser.open(url)
            except Exception as e:
                logger.error(f"開啟瀏覽器失敗: {e}")

        return True, port
    else:
        logger.error("伺服器看似啟動了，但無法連接，這可能表示啟動失敗")
        return False, 0


# 初始化系統托盤
def initialize_tray(server_port):
    """
    初始化系統托盤

    :param server_port: 伺服器端口
    :return: 托盤管理器
    """
    global tray_manager

    # 檢查是否啟用托盤功能
    if not config.get("tray", "enabled", True):
        logger.info("系統托盤功能已被禁用")
        return None

    # 創建並啟動托盤管理器
    tray_manager = TrayManager(
        server_url=f"http://localhost:{server_port}",
        shutdown_callback=shutdown_application,
    )
    tray_thread = tray_manager.run_in_thread()

    return tray_manager


# 應用程式入口
def main():
    """
    應用程式入口
    """
    try:
        app_title = config.get("app", "title", "Windows 使用者密碼修改工具")
        logger.info(f"啟動 {app_title}")

        # 確認應用所需的目錄結構
        logger.debug(f"確認目錄結構 - 應用目錄: {app_dir}")
        logger.debug(f"靜態目錄存在: {os.path.exists(static_dir)}")
        logger.debug(f"模板目錄存在: {os.path.exists(templates_dir)}")

        # 嘗試打印出模板文件列表
        try:
            template_files = os.listdir(templates_dir)
            logger.debug(f"模板文件列表: {template_files}")
        except Exception as e:
            logger.error(f"無法列出模板文件: {e}")

        # 嘗試啟動伺服器
        logger.info("開始啟動伺服器...")
        success, actual_port = run_server_in_thread(auto_find_port=True)

        if not success:
            logger.error("伺服器啟動失敗，應用程式將退出")
            return 1

        # 初始化系統托盤
        try:
            logger.info(f"開始初始化系統托盤，使用端口: {actual_port}")
            tray = initialize_tray(actual_port)
            if tray:
                logger.info("系統托盤初始化成功")
            else:
                logger.warning("系統托盤初始化失敗或被禁用")
        except Exception as e:
            logger.error(f"初始化系統托盤時發生錯誤: {e}")
            logger.exception("托盤初始化異常詳情")

        # 註冊信號處理函數
        signal.signal(signal.SIGINT, lambda sig, frame: shutdown_application())
        signal.signal(signal.SIGTERM, lambda sig, frame: shutdown_application())

        logger.info("應用程式初始化完成，進入主循環")

        try:
            # 等待停止信號
            while not stop_event.is_set():
                stop_event.wait(1)
        except KeyboardInterrupt:
            logger.info("收到鍵盤中斷信號")
            shutdown_application()
        except Exception as e:
            logger.error(f"主循環發生異常: {str(e)}")
            logger.exception("主循環中發生未預期的異常")
            return 1
        finally:
            logger.info("應用程式退出")

        return 0
    except Exception as e:
        logger.critical(f"應用程式啟動失敗: {e}")
        logger.exception("應用程式啟動過程中發生未預期的嚴重異常")
        return 1


# 啟動應用
if __name__ == "__main__":
    sys.exit(main())
