# Windows 用戶密碼修改應用

這是一個使用 FastAPI、Jinja2 和 Bootstrap 建立的應用程式，用於修改 Windows 使用者密碼。

## 功能特點

- 簡單的密碼修改界面
- 即時密碼匹配檢查，顯示綠色（匹配）或紅色（不匹配）提示
- 使用 FastAPI 和 Jinja2 實現 MTV 架構
- 美觀的 Bootstrap 界面設計
- 支援打包為獨立單一執行檔，並啟用 UAC 權限申請
- 完整的日誌記錄功能，記錄所有操作和錯誤
- 系統托盤圖標，方便操作和關閉應用
- 支援配置文件 (config.json)，可自定義設置

## 安裝與設置

1. 安裝所需依賴:
   ```
   pip install -r requirements.txt
   ```

2. 運行應用程式:
   ```
   python main.py
   ```

3. 訪問應用程式:
   打開瀏覽器並訪問 `http://localhost:18080`

## 配置文件 (config.json)

應用程式支援通過 `config.json` 文件進行自定義配置。第一次啟動時會自動創建默認配置文件。

### 配置項說明

```json
{
    "server": {
        "host": "0.0.0.0",      // 伺服器監聽的主機地址
        "port": 18080,          // 伺服器監聽的端口
        "auto_open_browser": true // 應用啟動時是否自動開啟瀏覽器
    },
    "logging": {
        "level": "INFO",        // 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        "max_file_size_mb": 10, // 單個日誌文件的最大大小 (MB)
        "backup_count": 5       // 保留的日誌文件備份數量
    },
    "tray": {
        "enabled": true,        // 是否啟用系統托盤功能
        "minimize_to_tray": true, // 最小化時是否縮小到託盤
        "close_to_tray": true   // 關閉窗口時是否最小化到託盤
    },
    "app": {
        "title": "Windows 使用者密碼修改工具", // 應用程式標題
        "locale": "zh-TW"       // 界面語言
    },
    "security": {
        "enable_password_masking": true, // 是否在日誌中遮罩密碼
        "log_user_actions": true         // 是否記錄用戶操作
    }
}
```

### 配置修改方式

有三種方式修改配置：

1. **直接編輯配置文件**：
   手動編輯 `config.json` 文件，重啟應用程式生效。

2. **通過 API 修改**：
   應用程式提供以下 API 端點用於配置管理：
   - `GET /api/config` - 獲取所有配置
   - `POST /api/config/{section}/{key}` - 修改特定配置項
   - `POST /api/config/reset` - 重置所有配置為默認值
   - `POST /api/config/reset?section={section}` - 重置特定配置區段

3. **程式化修改**：
   在程式中使用 `config_manager` 模組：
   ```python
   from config_manager import get_config
   
   config = get_config()
   port = config.get("server", "port", 18080)  # 獲取配置值
   config.set("server", "port", 8000)          # 設置配置值
   ```

## 系統托盤功能

應用程式會在系統托盤區域顯示一個圖標，提供以下功能：

### 托盤菜單選項

- **開啟應用**：在默認瀏覽器中打開應用頁面
- **查看日誌**：打開日誌文件目錄
- **退出**：完全關閉應用程式及其服務

### 使用方法

1. 啟動應用程式後，一個圖標會出現在系統托盤區域（通常在螢幕右下角的任務欄上）
2. 右鍵點擊圖標可以看到可用的操作菜單
3. 選擇「退出」來完全關閉應用

## 打包為單一執行檔

本專案提供了將應用程式打包為單一執行檔的功能，並且會自動啟用 UAC 權限請求。

### 打包步驟

1. 執行打包批處理文件:
   ```
   build.bat
   ```

2. 打包過程完成後，單一執行檔會生成在 `dist` 目錄中，名為 `Windows密碼修改工具.exe`。

3. 該執行檔可以直接複製到其他 Windows 電腦上使用，無需安裝 Python 或其他依賴。

### 打包優勢

- **單一檔案**: 所有程式碼、資源和依賴都打包在一個執行檔中
- **方便部署**: 無需安裝過程，直接複製即可使用
- **UAC 權限**: 自動請求管理員權限，確保能夠修改密碼
- **獨立運行**: 不需要安裝 Python 或其他庫

### 打包依賴

打包過程需要以下套件（已包含在 requirements.txt 中）:
- Nuitka: 用於將 Python 程式打包為執行檔
- Pillow: 用於創建應用程式圖標
- PySide6: 支援單一檔案打包
- Ordered-Set & Zstandard: Nuitka 的依賴項

## 日誌功能

應用程式提供了完整的日誌功能，記錄所有操作和錯誤，有助於問題診斷和安全審計。

### 日誌特點

- **每日日誌文件**: 日誌按日期自動分割，便於查閱
- **自動輪轉**: 日誌文件超過指定大小後自動輪轉，防止磁碟空間耗盡
- **多級日誌**: 支援不同級別的日誌記錄（DEBUG、INFO、WARNING、ERROR）
- **密碼安全**: 日誌中的密碼會被遮罩，確保安全性
- **完整記錄**: 記錄所有密碼修改操作，包括成功與失敗的嘗試

### 日誌文件位置

- **開發模式**: 日誌文件位於專案目錄下的 `logs` 資料夾
- **打包版本**: 日誌文件位於執行檔所在目錄下的 `logs` 資料夾

查看日誌文件的命名格式為 `password_change_YYYY-MM-DD.log`，其中 YYYY-MM-DD 為日期。

## 注意事項

- 此應用程式需要在 Windows 操作系統上運行
- 執行程式的用戶需要具有適當的權限來修改其他用戶的密碼
- 打包後的執行檔會自動請求管理員權限，以確保能夠修改密碼
- 所有密碼修改操作都會被記錄到日誌文件中，但密碼本身會被遮罩處理
- 關閉應用時請使用系統托盤中的「退出」選項，以確保應用正確關閉
- 可以通過編輯 `config.json` 配置文件調整應用行為 