import sys
import re
from io import StringIO
import subprocess

# 导入工具类
if __name__ == "__main__":
    from tools import Tools
else:
    from sources.tools.tools import Tools


class BashInterpreter(Tools):
    """
    BashInterpreter 类是一个允许代理执行 bash 代码的工具。
    """

    def __init__(self):
        super().__init__()
        self.tag = "bash"  # 设置工具标签为 bash

    def language_bash_attempt(self, command: str):
        """
        检测AI是否尝试通过 bash 执行代码。
        如果是，返回 True，否则返回 False。
        理念是，AI编写的代码应该被执行，因此它不应该通过 bash 来运行它。
        """
        lang_interpreter = ["python3", "gcc", "g++", "go", "javac", "rustc", "clang", "clang++", "rustc", "rustc++",
                            "rustc++"]
        for word in command.split():  # 遍历命令的每一部分
            if word in lang_interpreter:  # 如果命令包含编译器或解释器关键词
                return True
        return False

    def execute(self, commands: str, safety=False, timeout=1000):
        """
        执行 bash 命令并实时显示输出。
        """
        if safety and input("是否执行命令? y/n ") != "y":  # 安全检查，确保用户同意执行命令
            return "命令被用户拒绝。"

        concat_output = ""
        for command in commands:
            if self.language_bash_attempt(command):  # 如果是 AI 尝试执行代码，则跳过
                continue
            try:
                # 使用 subprocess 执行命令并获取输出
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                command_output = ""
                for line in process.stdout:  # 实时输出命令执行结果
                    print(line, end="")
                    command_output += line
                return_code = process.wait(timeout=timeout)  # 等待命令执行完成并检查超时
                if return_code != 0:  # 如果命令返回失败
                    return f"命令 {command} 执行失败，返回码 {return_code}：\n{command_output}"
                concat_output += f"命令 {command} 的输出：\n{command_output.strip()}\n\n"
            except subprocess.TimeoutExpired:
                process.kill()  # 如果超时，则终止进程
                return f"命令 {command} 超时，输出：\n{command_output}"
            except Exception as e:
                return f"命令 {command} 执行失败：\n{str(e)}"
        return concat_output

    def interpreter_feedback(self, output):
        """
        根据 bash 执行器的输出提供反馈。
        """
        if self.execution_failure_check(output):  # 如果执行失败，检查失败的反馈
            feedback = f"[失败] 执行出错：\n{output}"
        else:
            feedback = "[成功] 执行成功，代码输出：\n" + output
        return feedback

    def execution_failure_check(self, feedback):
        """
        检查 bash 命令是否失败。
        """
        error_patterns = [
            r"expected",
            r"errno",
            r"failed",
            r"invalid",
            r"unrecognized",
            r"exception",
            r"syntax",
            r"segmentation fault",
            r"core dumped",
            r"unexpected",
            r"denied",
            r"not recognized",
            r"not permitted",
            r"not installed",
            r"not found",
            r"no such",
            r"too many",
            r"too few",
            r"busy",
            r"broken pipe",
            r"missing",
            r"undefined",
            r"refused",
            r"unreachable",
            r"not known"
        ]
        combined_pattern = "|".join(error_patterns)  # 合并所有错误模式为一个正则表达式
        if re.search(combined_pattern, feedback, re.IGNORECASE):  # 如果反馈中包含错误模式
            return True
        return False


if __name__ == "__main__":
    bash = BashInterpreter()  # 创建 BashInterpreter 实例
    print(bash.execute(["ls", "pwd", "ip a", "nmap -sC 127.0.0.1"]))  # 执行多个 bash 命令
