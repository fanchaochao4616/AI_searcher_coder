import sys
import os
import re
from io import StringIO

# 导入工具类
if __name__ == "__main__":
    from tools import Tools
else:
    from sources.tools.tools import Tools


class PyInterpreter(Tools):
    """
    PyInterpreter 类是一个工具，允许代理执行 Python 代码。
    """

    def __init__(self):
        super().__init__()
        self.tag = "python"  # 设置工具标签为 python

    def execute(self, codes: str, safety=False) -> str:
        """
        执行 Python 代码。
        参数:
            codes (str): 要执行的 Python 代码
            safety (bool): 是否进行安全确认
        返回:
            str: 执行结果
        """
        output = ""
        # 安全检查，确保用户同意执行代码
        if safety and input("是否执行代码？ y/n") != "y":
            return "代码被用户拒绝。"

        stdout_buffer = StringIO()  # 捕获标准输出
        sys.stdout = stdout_buffer
        global_vars = {
            '__builtins__': __builtins__,
            'os': os,
            'sys': sys,
        }
        code = '\n\n'.join(codes)  # 将代码合并为一个字符串
        try:
            try:
                buffer = exec(code, global_vars)  # 执行代码
                if buffer is not None:
                    output = buffer + '\n'
            except Exception as e:
                return "代码执行失败: " + str(e)
            output = stdout_buffer.getvalue()  # 获取输出结果
        finally:
            sys.stdout = sys.__stdout__  # 恢复标准输出
        return output

    def interpreter_feedback(self, output: str) -> str:
        """
        根据代码执行的输出提供反馈。
        参数:
            output (str): 执行结果
        返回:
            str: 反馈消息
        """
        if self.execution_failure_check(output):  # 如果执行失败，返回错误反馈
            feedback = f"[失败] 执行出错：\n{output}"
        else:
            feedback = "[成功] 执行成功，代码输出：\n" + output
        return feedback

    def execution_failure_check(self, feedback: str) -> bool:
        """
        检查代码执行是否失败。
        参数:
            feedback (str): 执行结果
        返回:
            bool: 如果执行失败，返回 True，否则返回 False
        """
        error_patterns = [
            r"expected",  # 期望错误
            r"errno",  # 错误号
            r"failed",  # 失败
            r"traceback",  # 错误堆栈
            r"invalid",  # 无效
            r"unrecognized",  # 无法识别
            r"exception",  # 异常
            r"syntax",  # 语法错误
            r"crash",  # 崩溃
            r"segmentation fault",  # 段错误
            r"core dumped"  # 核心转储
        ]
        combined_pattern = "|".join(error_patterns)  # 合并所有错误模式为一个正则表达式
        if re.search(combined_pattern, feedback, re.IGNORECASE):  # 如果反馈中包含错误模式
            return True
        return False


if __name__ == "__main__":
    text = """
Python 示例：

```python
print("Hello from Python!")
如果这些代码能成功运行，你将在下一条消息中看到输出结果。如果你有其他想要测试的内容，请告诉我！

这是一个保存测试：
    def print_hello():
        hello = "Hello World"
        print(hello)
"""
py = PyInterpreter() # 创建 PyInterpreter 实例
codes, save_path = py.load_exec_block(text) # 加载并执行代码块
py.save_block(codes, save_path) # 保存代码块
print(py.execute(codes)) # 执行 Python 代码并输出结果