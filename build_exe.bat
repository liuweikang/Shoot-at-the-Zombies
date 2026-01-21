@echo off
echo 开始打包游戏机器人...
echo.

REM 使用PyInstaller打包，--windowed表示不显示控制台窗口，--onefile表示生成单个exe文件
REM --add-data参数用于包含templates目录，格式为 "源路径;目标路径"
pyinstaller --onefile --name="游戏机器人" --add-data "templates;templates" game_bot.py

echo.
echo 打包完成！
echo 可执行文件位于 dist/游戏机器人.exe
pause