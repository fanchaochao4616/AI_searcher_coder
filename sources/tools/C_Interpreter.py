import subprocess
import os
import tempfile
import re

# 导入工具类
if __name__ == "__main__":
    from tools import Tools
else:
    from sources.tools.tools import Tools

class CInterpreter(Tools):
    """
    CInterpreter 类是一个允许代理执行 C 代码的工具。
    """
    def __init__(self):
        super().__init__()
        self.tag = "c"  # 设置工具标签为 c

    def execute(self, codes: str, safety=False) -> str:
        """
        通过编译和运行 C 代码来执行。
        """
        output = ""
        code = '\n'.join(codes) if isinstance(codes, list) else codes  # 将代码列表转换为字符串

        # 安全检查：如果用户拒绝执行代码，则返回拒绝信息
        if safety and input("是否执行代码? y/n ") != "y":
            return "代码被用户拒绝。"

        # 根据操作系统决定执行文件的扩展名
        exec_extension = ".exe" if os.name == "nt" else ""  # Windows 使用 .exe，Linux/Unix 不使用

        # 使用临时目录存储源代码和执行文件
        with tempfile.TemporaryDirectory() as tmpdirname:
            source_file = os.path.join(tmpdirname, "temp.c")  # C 源代码文件路径
            exec_file = os.path.join(tmpdirname, "temp") + exec_extension  # 编译后的执行文件路径

            # 将 C 代码写入源文件
            with open(source_file, 'w') as f:
                f.write(code)

            try:
                # 编译命令
                compile_command = ["gcc", source_file, "-o", exec_file]
                compile_result = subprocess.run(
                    compile_command,
                    capture_output=True,
                    text=True,
                    timeout=10  # 编译超时设置为 10 秒
                )

                # 如果编译失败，返回编译错误信息
                if compile_result.returncode != 0:
                    return f"编译失败: {compile_result.stderr}"

                # 运行命令
                run_command = [exec_file]
                run_result = subprocess.run(
                    run_command,
                    capture_output=True,
                    text=True,
                    timeout=10  # 运行超时设置为 10 秒
                )

                # 如果执行失败，返回执行错误信息
                if run_result.returncode != 0:
                    return f"执行失败: {run_result.stderr}"
                output = run_result.stdout  # 获取执行输出

            except subprocess.TimeoutExpired as e:
                return f"执行超时: {str(e)}"
            except FileNotFoundError:
                return "错误: 未找到 'gcc'。请确保已安装 C 编译器（如 gcc）并添加到 PATH 中。"
            except Exception as e:
                return f"代码执行失败: {str(e)}"

        return output

    def interpreter_feedback(self, output: str) -> str:
        """
        根据代码执行的输出提供反馈。
        """
        if self.execution_failure_check(output):  # 如果执行失败，检查失败的反馈
            feedback = f"[失败] 执行出错：\n{output}"
        else:
            feedback = "[成功] 执行成功，代码输出：\n" + output
        return feedback

    def execution_failure_check(self, feedback: str) -> bool:
        """
        检查代码执行是否失败。
        """
        error_patterns = [
            r"error",  # 错误
            r"failed",  # 失败
            r"traceback",  # 跟踪信息
            r"invalid",  # 无效
            r"exception",  # 异常
            r"syntax",  # 语法错误
            r"segmentation fault",  # 段错误
            r"core dumped",  # 核心转储
            r"undefined",  # 未定义
            r"cannot"  # 不能
        ]
        combined_pattern = "|".join(error_patterns)  # 合并所有错误模式为一个正则表达式
        if re.search(combined_pattern, feedback, re.IGNORECASE):  # 如果反馈中包含任何错误模式
            return True
        return False

if __name__ == "__main__":
    # 示例 C 代码
    codes = [
"""
#include <stdio.h>
#include <stdlib.h>

void hello() {
    printf("Hello, World!\\n");
}
""",
"""
int main() {
    hello();
    return 0;
}
    """
    ]
    c = CInterpreter()  # 创建 CInterpreter 实例
    print(c.execute(codes))  # 执行 C 代码并输出结果
