from colorama import Fore
from termcolor import colored
import platform
import threading
import itertools
import time


def pretty_print(text, color = "info"):
    """
    打印带有颜色格式的文本。

    参数:
        text (str): 要打印的文本
        color (str, 可选): 要使用的颜色，默认为"info"。支持的颜色如下：
            - "success": 绿色，表示成功
            - "failure": 红色，表示失败
            - "status": 浅绿色，表示状态信息
            - "code": 浅蓝色，表示代码
            - "warning": 黄色，表示警告
            - "output": 浅青色，表示输出
            - "default": 黑色（仅限Windows系统）
    """
    if platform.system().lower() != "windows":
        # 非Windows系统使用colorama的颜色
        color_map = {
            "success": Fore.GREEN,
            "failure": Fore.RED,
            "status": Fore.LIGHTGREEN_EX,
            "code": Fore.LIGHTBLUE_EX,
            "warning": Fore.YELLOW,
            "output": Fore.LIGHTCYAN_EX,
            "info": Fore.CYAN
        }
        # 如果颜色不在color_map中，则打印文本并发出警告
        if color not in color_map:
            print(text)
            pretty_print(f"Invalid color {color} in pretty_print", "warning")
            return
        # 打印带颜色的文本
        print(color_map[color], text, Fore.RESET)
    else:
        # Windows系统使用termcolor的颜色
        color_map = {
            "success": "green",
            "failure": "red",
            "status": "light_green",
            "code": "light_blue",
            "warning": "yellow",
            "output": "cyan",
            "default": "black"
        }
        if color not in color_map:
            color = "default"  # 如果颜色无效，使用默认颜色
        # 打印带颜色的文本
        print(colored(text, color_map[color]))


def animate_thinking(text, color="status", duration=2):
    """
    显示一个“正在思考...”的动画，运行在单独的线程中。

    参数:
        text (str): 要显示的文本
        color (str): 文本的颜色
        duration (float): 动画持续时间（秒）
    """
    def _animate():
        # 定义颜色映射
        color_map = {
            "success": (Fore.GREEN, "green"),
            "failure": (Fore.RED, "red"),
            "status": (Fore.LIGHTGREEN_EX, "light_green"),
            "code": (Fore.LIGHTBLUE_EX, "light_blue"),
            "warning": (Fore.YELLOW, "yellow"),
            "output": (Fore.LIGHTCYAN_EX, "cyan"),
            "default": (Fore.RESET, "black"),
            "info": (Fore.CYAN, "cyan")
        }

        # 获取颜色对应的控制码
        fore_color, term_color = color_map[color]
        # 定义旋转的动画符号（圆圈的动态效果）
        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        end_time = time.time() + duration  # 结束时间

        # 在指定的时间内持续更新动画
        while time.time() < end_time:
            symbol = next(spinner)  # 获取下一个旋转符号
            if platform.system().lower() != "windows":
                # 非Windows系统使用colorama显示带颜色的动画
                print(f"\r{fore_color}{symbol} {text}{Fore.RESET}", end="", flush=True)
            else:
                # Windows系统使用termcolor显示带颜色的动画
                print(colored(f"\r{symbol} {text}", term_color), end="", flush=True)
            time.sleep(0.1)  # 每次更新间隔0.1秒
        print()  # 在结束时换行

    # 创建并启动动画线程
    animation_thread = threading.Thread(target=_animate)
    animation_thread.daemon = True  # 设置为守护线程
    animation_thread.start()


def timer_decorator(func):
    """
    装饰器，用于计算函数的执行时间并打印。

    用法:
    @timer_decorator
    def my_function():
        # 要执行的代码
    """
    from time import time
    def wrapper(*args, **kwargs):
        start_time = time()  # 获取开始时间
        result = func(*args, **kwargs)  # 执行原函数
        end_time = time()  # 获取结束时间
        print(f"{func.__name__} 执行了 {end_time - start_time:.2f} 秒")  # 打印执行时间
        return result  # 返回原函数的结果

    return wrapper  # 返回包装函数
