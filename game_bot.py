from cv2.gapi.streaming import timestamp
import pyautogui
import cv2
import numpy as np
from win32 import win32gui
import time
import random
import os
import sys
import argparse
from pynput import keyboard
import tkinter as tk
from tkinter import ttk, messagebox
import threading

class GameBot:
    def __init__(self, game_title="游戏窗口标题", battle_time=0, battle_count=0, mode=0, skill_sort=""):
        self.running = True
        self.hotkey_listener = None
        """初始化游戏机器人"""
        self.game_title = game_title
        self.battle_time = battle_time
        self.battle_count = battle_count
        self.game_window = None
        self.screenshot_dir = "screenshots"
        self.template_dir = "templates"
        self.mode = mode
        self.skill_sort = skill_sort

        # 创建必要的目录
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.template_dir, exist_ok=True)

    def find_game_window(self):
        """查找并激活游戏窗口"""
        hwnd = win32gui.FindWindow(None, self.game_title)
        if hwnd:
            win32gui.SetForegroundWindow(hwnd)
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            self.game_window = (left, top, right-left, bottom-top)
            print(f"找到游戏窗口: {self.game_window}")
            return True
        else:
            print("未找到游戏窗口")
            return False

    def find_fullscreen_window(self):
        """查找全屏幕窗口"""
        # 使用pyautogui获取屏幕尺寸，更简单可靠
        try:
            # 获取主屏幕尺寸
            width, height = pyautogui.size()
            left, top = 0, 0
            self.game_window = (left, top, width, height)
            print(f"全屏幕窗口: {self.game_window}")
            return True
        except Exception as e:
            print(f"获取屏幕尺寸时出错: {e}")
            # 如果pyautogui失败，尝试使用win32gui的基本方法
            try:
                width = win32gui.GetSystemMetrics(0)  # SM_CXSCREEN
                height = win32gui.GetSystemMetrics(1) # SM_CYSCREEN
                left, top = 0, 0
                self.game_window = (left, top, width, height)
                print(f"使用备用方法获取全屏幕窗口: {self.game_window}")
                return True
            except Exception as e2:
                print(f"备用方法也失败: {e2}")
                return False
    def take_screenshot(self):
        """截取游戏窗口画面"""
        if not self.game_window:
            if not self.find_game_window():
                return None
        
        screenshot = pyautogui.screenshot(region=self.game_window)
        return screenshot

    def save_screenshot(self, filename=None):
        """保存截图"""
        screenshot = self.take_screenshot()
        if screenshot:
            if not filename:
                filename = f"{self.screenshot_dir}/{int(time.time())}.png"
            screenshot.save(filename)
            print(f"截图已保存: {filename}")
            return filename
        return None

    def find_template(self, template_name, threshold=0.8):
        """在游戏窗口中查找模板图像"""
        template_path = os.path.join(self.template_dir, template_name)

        """在游戏窗口中查找模板图像"""
        screenshot = self.take_screenshot()
        if not screenshot:
            return None
        
        # 转换为OpenCV格式
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(template_path)
        
        if template is None:
            print(f"无法加载模板: {template_path}")
            return None
        
        # 模板匹配
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            h, w = template.shape[:2]
            center_x = self.game_window[0] + max_loc[0] + w // 2
            center_y = self.game_window[1] + max_loc[1] + h // 2
            print(f"找到匹配: {template_path}, 位置: ({center_x}, {center_y}), 相似度: {max_val:.2f}")
            return (center_x, center_y)
        
        # print(f"未找到匹配: {template_path}")
        return None

    def find_all_templates(self, template_name, threshold=0.8):
        """在游戏窗口中查找所有匹配的模板图像位置"""
        template_path = os.path.join(self.template_dir, template_name)
        
        screenshot = self.take_screenshot()
        if not screenshot:
            return []
        
        # 转换为OpenCV格式
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(template_path)
        
        if template is None:
            print(f"无法加载模板: {template_path}")
            return []
        
        # 模板匹配
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        
        # 获取所有超过阈值的匹配位置
        locations = np.where(result >= threshold)
        matches = []
        
        # 获取模板尺寸
        h, w = template.shape[:2]
        
        # 处理找到的匹配位置
        for pt in zip(*locations[::-1]):  # 切换x和y坐标
            center_x = self.game_window[0] + pt[0] + w // 2
            center_y = self.game_window[1] + pt[1] + h // 2
            matches.append((center_x, center_y))
            print(f"找到匹配: {template_path}, 位置: ({center_x}, {center_y})")
        
        return matches

    def click(self, x, y, duration=0.2, human_like=True):
        """模拟鼠标点击"""
        if human_like:
            # 添加随机偏移，模拟人类点击
            x += random.randint(-5, 5)
            y += random.randint(-5, 5)
            duration += random.uniform(-0.1, 0.1)
            duration = max(0.1, duration)
        
        pyautogui.moveTo(x, y, duration=duration)
        pyautogui.click()
        print(f"点击位置: ({x}, {y})")
    
    def click_fast(self, x, y):
        """快速点击，不添加随机偏移和移动时间"""
        pyautogui.moveTo(x, y, duration=0)
        pyautogui.click()
        print(f"快速点击位置: ({x}, {y})")

    def press_key(self, key, presses=1, interval=0.1, human_like=True):
        """模拟按键"""
        if human_like:
            interval += random.uniform(-0.05, 0.05)
            interval = max(0.05, interval)
        
        pyautogui.press(key, presses=presses, interval=interval)
        print(f"按下按键: {key}")

    def find_im(self):
        """判断能否发现环球页面"""
        im = self.find_template("im.png")
        if im:
            self.click(*im)
            time.sleep(1)

    def find_click_continue(self):
        """判断能否发现继续按钮"""
        continue_button = self.find_template("click-continue.png")
        if continue_button:
            self.click(*continue_button)
            time.sleep(0.2)
    def find_team_up(self):
        """判断能否发现队伍页面"""
        return self.find_template("team-up.png")
    def find_recruitment(self):
        while True and self.running:
            """判断能否发现招募页面"""
            team_up = self.find_team_up()
            if not team_up:
                xy = self.find_template("recruitment.png")
                if not xy:
                    xy = self.find_template("recruitment-1.png")
                if xy:
                    self.click(*xy)
                    time.sleep(0.2)
                else:
                    break
            self.find_reconnection()
            for i in range(20):
                try:
                    huanqiu_positions = self.find_all_templates("huanqiu.png")
                    if huanqiu_positions:
                        # 使用快速点击方法点击所有找到的环球按钮
                        for pos in huanqiu_positions:
                            self.click_fast(*pos)
                    else:
                        print("未找到环球按钮")
                        time.sleep(0.1)  # 减少等待时间
                except:
                    print("查找环球按钮时出错")
                    time.sleep(0.1)  # 减少等待时间
                else:
                    print("未找到招募页面")
            
    def find_in_huanqiu_team(self):
        """是否在环球队伍"""
        huanqiu_team = self.find_template("in-huanqiu-team.png")
        if huanqiu_team:
            time.sleep(6)
    def find_home_close(self):
        """判断能否发现关闭按钮"""
        close = self.find_template("home-close.png")
        if not close:
            close = self.find_template("home-close-1.png")
        
        if not close and self.find_template("home-close-2-text.png"):
            close = self.find_template("home-close-2.png")
            
        if close:
            self.click(*close)
            time.sleep(0.2)

    def find_close(self):
        """判断能否发现关闭按钮"""
        close = self.find_template("close.png")
        if close:
            self.click(*close)
            time.sleep(0.2)
    def find_reconnection(self):
        """判断能否发现重新连接按钮"""
        reconnection = self.find_template("reconnection.png")
        if reconnection:
            self.click(*reconnection)
            time.sleep(0.2)
    def find_huanqiu(self):
        """判断能否发现环球按钮"""
        return self.find_template("huanqiu.png")

    def find_start_button(self):
        """找到战斗位置"""
        battle = self.find_template("battle.png")
        if not battle:
            battle = self.find_template("battle-1.png")
        if battle:
            self.click(*battle)
            time.sleep(0.2)
            return True
        return False
    def find_sure(self):
        """判断能否发现确定按钮"""
        sure = self.find_template("sure.png")
        if sure:
            self.click(*sure)
            time.sleep(0.2)
    def find_battling_continue(self):
        """判断能否发现继续战斗按钮"""
        continue_battle = self.find_template("battling-continue.png")
        if continue_battle:
            self.click(*continue_battle)
            time.sleep(0.2)
    def find_skill(self):
        """判断能否发现技能按钮"""
        # 如果没有提供自定义顺序，则使用默认顺序
        if self.skill_sort == "":
            skills = ["skill"]
            for i in range(1, 11):
                skills.append(f"skill-{i}")
        else:
            # 使用自定义顺序
            skills = self.skill_sort.split(",")
        
        for skill in skills:
            # 确保文件名包含.png扩展名
            if not skill.endswith('.png'):
                skill = f"{skill}.png"
            
            skill_pos = self.find_template(skill)
            if skill_pos:
                self.click(*skill_pos)
                time.sleep(0.2)
                return None
        return None
        
    def find_battling(self):
        """判断是否在战斗中"""
        xy = self.find_template("battling.png")
        if not xy:
            xy = self.find_template("battling-2.png")
        if not xy:
            xy = self.find_template("battling-3.png")
        if not xy:
            xy = self.find_template("battling-4.png")
        if not xy:
            xy = self.find_template("battling-5.png")
        return xy

    def find_dont_battle_return(self):
        """判断是否有返回按钮"""
        return_button = self.find_template("return-1.png")
        if return_button:
            self.click(*return_button)
            time.sleep(0.2)
    def find_return(self):
        """判断是否在返回主界面"""
        return_button = self.find_template("return.png")
        if return_button:
            self.click(*return_button)
            time.sleep(0.2)
    def find_stop(self):
        """判断能否发现停止按钮"""
        stop = self.find_template("battling.png")
        if stop:
            self.click(*stop)
            time.sleep(0.2)
    def find_exit(self):
        """判断能否发现退出按钮"""
        exit_button = self.find_template("exit.png")
        if exit_button:
            self.click(*exit_button)
            time.sleep(0.2)
    def find_card(self):
        """判断能否发现卡关按钮"""
        card = self.find_template("card-normal.png")
        if card:
            self.click(*card)
            time.sleep(0.2)
            card = self.find_template("card-start.png")
            if card:
                self.click(*card)
                time.sleep(0.2)
    def find_orange_start_game(self):
        """判断能否发现橘子开始游戏按钮"""
        orange_start_game = self.find_template("orange-start.png")
        print(orange_start_game)
        if orange_start_game:
            self.click(*orange_start_game)
            time.sleep(0.2)
    def on_hotkey(self, key):
        """快捷键回调函数"""
        try:
            if key == keyboard.Key.esc:
                print("检测到ESC键，正在停止脚本...")
                self.running = False
                if self.hotkey_listener:
                    self.hotkey_listener.stop()
                return False
        except AttributeError:
            pass
        return True

    def setup_hotkey(self):
        """设置快捷键监听"""
        print("已设置快捷键: ESC键 - 停止脚本")
        self.hotkey_listener = keyboard.Listener(on_release=self.on_hotkey)
        self.hotkey_listener.start()

    def main_loop(self, iterations=None):
        """主循环"""
        # 设置快捷键监听
        self.setup_hotkey()
        
        print("开始自动刷图脚本...")
        print("提示: 按下ESC键可以随时停止脚本")
        count = self.battle_count
        
        # timestamp = time.time()
        while self.running:
            # 检查是否达到迭代次数
            if iterations and count >= iterations:
                print(f"已完成 {iterations} 次刷图，脚本停止")
                self.running = False
                break
            
            # 确保游戏窗口被找到
            if not self.game_window and not self.find_game_window():
                time.sleep(5)
                continue
            # 关闭按钮
            self.find_home_close()
            
            # 检查是否需要重新连接
            self.find_reconnection()
            
            # 是否确定
            self.find_sure()
            
            # 是不是通关了
            self.find_return()

            batileTime = None
            # 是不是在战斗中
            while True and self.running:

                if self.mode == 2:
                    self.find_fullscreen_window()
                    # 检查开始游戏是否可点击
                    self.find_orange_start_game()
                    time.sleep(10)
                    continue

                battling = self.find_battling()
                if not battling:
                    break
                print("正在战斗中")
                # 点击技能
                self.find_skill()
                # 点击继续战斗
                self.find_battling_continue()
                time.sleep(3)
                # 点击重新连接
                self.find_reconnection()
                # 关闭窗口
                self.find_close()
                # 点击返回
                self.find_return()

                if batileTime is None:
                    batileTime = time.time()
                else:
                    if self.battle_time > 0 and time.time() - batileTime > self.battle_time:
                        print(f"战斗时间超过{self.battle_time}秒,退出")
                        self.find_stop()
                        self.find_exit()
                print("战斗时间:", time.time() - batileTime)
            # 是否刷环球
            if self.mode == 0:
                # 先找是不是在招募中
                self.find_recruitment()
                # 是否在环球队伍 等6秒
                self.find_in_huanqiu_team()
                

            # 先确定位置
            start_button = self.find_start_button()
            if not start_button:
                # 不打远征
                self.find_dont_battle_return()
                self.find_click_continue()
                continue
            # 是否刷环球
            if self.mode == 0:
                # 检查当前页面是否在环球页面
                self.find_im()
            # 是否刷卡关
            if self.mode == 1:
                # 检查当前页面是否在卡关页面
                self.find_card()
            # 点击继续
            self.find_click_continue()
            # 每100秒随机点个位置
            # if time.time() - timestamp > 100:
                # 随机点击
                # self.click(random.randint(int(self.game_window[2]), int(self.game_window[0])), random.randint(int(self.game_window[1]), int(self.game_window[3])))
                # self.click(500, 100)
                # timestamp = time.time()

class GameBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏机器人操作界面")
        self.root.geometry("600x600")
        self.root.resizable(False, False)
        
        self.bot = None
        self.is_running = False
        
        # 创建界面组件
        self.create_widgets()
    
    def create_widgets(self):
        # 游戏标题
        ttk.Label(self.root, text="游戏窗口标题:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.game_title_var = tk.StringVar(value="向僵尸开炮")
        ttk.Entry(self.root, textvariable=self.game_title_var, width=30).grid(row=0, column=1, padx=10, pady=5)
        
        # 模式选择
        ttk.Label(self.root, text="模式:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.mode_var = tk.IntVar(value=0)
        mode_frame = ttk.Frame(self.root)
        mode_frame.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="打环球", variable=self.mode_var, value=0).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="刷卡关", variable=self.mode_var, value=1).pack(side=tk.LEFT)
        # ttk.Radiobutton(mode_frame, text="全屏模式", variable=self.mode_var, value=2).pack(side=tk.LEFT)
        
        # 战斗次数
        ttk.Label(self.root, text="战斗次数:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.battle_count_var = tk.IntVar(value=0)
        ttk.Spinbox(self.root, from_=0, to=999, textvariable=self.battle_count_var, width=10).grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)
        ttk.Label(self.root, text="(0表示无限循环)").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        
        # 战斗时间
        ttk.Label(self.root, text="战斗时间(秒):").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        self.battle_time_var = tk.IntVar(value=0)
        ttk.Spinbox(self.root, from_=0, to=999, textvariable=self.battle_time_var, width=10).grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)
        ttk.Label(self.root, text="(0表示无限制)").grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)
        
        # 技能顺序
        ttk.Label(self.root, text="技能顺序:").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        self.skill_sort_var = tk.StringVar(value="")
        ttk.Entry(self.root, textvariable=self.skill_sort_var, width=30).grid(row=4, column=1, padx=10, pady=5, columnspan=2)
        ttk.Label(self.root, text="(用逗号分隔，如: skill,skill-1)").grid(row=5, column=1, padx=10, pady=5, columnspan=2, sticky=tk.W)
        
        # 按钮框架
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=6, column=0, columnspan=3, padx=10, pady=20)
        
        # 开始按钮
        self.start_btn = ttk.Button(button_frame, text="开始", command=self.start_bot, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        # 停止按钮
        self.stop_btn = ttk.Button(button_frame, text="停止", command=self.stop_bot, width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # 退出按钮
        self.quit_btn = ttk.Button(button_frame, text="退出", command=self.quit_app, width=15)
        self.quit_btn.pack(side=tk.LEFT, padx=10)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.root, textvariable=self.status_var, foreground="green").grid(row=7, column=0, columnspan=3, padx=10, pady=10)
    
    def start_bot(self):
        """开始运行游戏机器人"""
        try:
            # 获取界面参数
            game_title = self.game_title_var.get()
            mode = self.mode_var.get()
            battle_count = self.battle_count_var.get()
            battle_time = self.battle_time_var.get()
            skill_sort = self.skill_sort_var.get()
            
            # 验证参数
            if not game_title:
                messagebox.showerror("错误", "请输入游戏窗口标题")
                return
            
            # 创建GameBot实例
            self.bot = GameBot(game_title, battle_time, battle_count, mode, skill_sort)
            
            # 更新状态
            self.status_var.set("运行中...")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # 创建并启动线程
            self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            self.bot_thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {str(e)}")
            self.status_var.set("就绪")
    
    def run_bot(self):
        """运行游戏机器人主循环"""
        try:
            # 运行主循环，直到达到指定次数或被停止
            while self.bot and self.bot.running:
                # 运行一次主循环迭代
                self.bot.main_loop(iterations=1)
                # 短暂休眠，避免CPU占用过高
                time.sleep(0.1)
        except Exception as e:
            print(f"运行出错: {str(e)}")
        finally:
            # 停止运行
            self.root.after(0, self.stop_bot)
    
    def stop_bot(self):
        """停止游戏机器人"""
        if self.bot:
            self.bot.running = False
            self.bot = None
        
        # 更新状态
        self.status_var.set("已停止")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
    
    def quit_app(self):
        """退出应用程序"""
        if self.bot:
            self.bot.running = False
        self.root.quit()

if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    
    # 设置窗口图标（可选）
    try:
        root.iconbitmap(default=None)
    except:
        pass
    
    # 创建GUI实例
    app = GameBotGUI(root)
    
    # 运行主循环
    root.mainloop()

# 使用说明:
# 1. 安装必要的依赖: pip install pyautogui opencv-python pillow pynput pywin32
# 2. 替换脚本中的游戏窗口标题为你的游戏窗口标题
# 3. 在 templates 文件夹中添加游戏界面元素的截图作为模板
# 4. 运行脚本: python game_bot.py
# 5. 脚本会自动查找游戏窗口，开始战斗，收集奖励
#
# 注意事项:
# - 本脚本仅提供基础框架，需要根据具体游戏进行调整
# - 为了提高识别准确率，建议使用游戏窗口的原始分辨率
# - 使用时请确保游戏窗口未被遮挡
# - 可以通过添加更多的模板和状态判断来提高脚本的智能性
# - 游戏过程中尽量不要操作鼠标和键盘，以免干扰脚本运行