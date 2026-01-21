@echo off
echo 开始打包游戏机器人...
echo.

REM 使用PyInstaller打包，--windowed表示不显示控制台窗口，--onefile表示生成单个exe文件
pyinstaller --windowed --onefile --name="游戏机器人" game_bot.py

echo.
echo 打包完成！
echo 可执行文件位于 dist/游戏机器人.exe
pause