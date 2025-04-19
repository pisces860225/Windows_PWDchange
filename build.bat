@echo off
echo Windows密碼修改工具 - 打包腳本 (單一執行檔模式)
echo ===========================================
echo.

REM 確認已安裝所需的套件
echo 檢查並安裝所需的套件...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 安裝套件失敗，請手動執行 pip install -r requirements.txt
    pause
    exit /b 1
)

REM 創建圖標
echo 創建應用程式圖標...
python create_icon.py
if %errorlevel% neq 0 (
    echo 圖標創建失敗，但會繼續執行打包過程。
)

REM 執行打包腳本
echo.
echo 開始執行打包過程...
echo 正在將應用程式打包為單一執行檔，這可能需要幾分鐘時間...
python build.py
if %errorlevel% neq 0 (
    echo 打包過程失敗。
    pause
    exit /b 1
)

echo.
echo 打包過程完成！
echo 單一執行檔位於 dist 目錄中的 Windows密碼修改工具.exe
echo.
echo 該執行檔包含了所有必需的文件，可以直接複製到其他電腦上運行
echo 注意：運行時需要管理員權限
echo.
echo 按任意鍵打開 dist 目錄...
pause > nul
start "" dist 