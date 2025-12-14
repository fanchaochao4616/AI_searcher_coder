import subprocess
import os
import tempfile
import re

# 导入工具类
if __name__ == "__main__":
    from tools import Tools
else:
    from sources.tools.tools import Tools

class GoInterpreter(Tools):
    """
    GoInterpreter 类是一个工具，允许执行 Go 代码。
    """
    def __init__(self):
        super().__init__()
        self.tag = "go"  # 设置工具标签为 go

    def execute(self, codes: str, safety=False) -> str:
        """
        通过编译和运行 Go 代码来执行。
        参数:
            codes (str): 要执行的 Go 代码
            safety (bool): 是否需要安全确认
        返回:
            str: 执行结果
        """
        output = ""
        code = '\n'.join(codes) if isinstance(codes, list) else codes  # 如果是列表，合并成字符串

        # 安全检查，确保用户同意执行代码
        if safety and input("是否执行代码? y/n ") != "y":
            return "代码被用户拒绝。"

        # 使用临时目录来存储源代码和可执行文件
        with tempfile.TemporaryDirectory() as tmpdirname:
            source_file = os.path.join(tmpdirname, "temp.go")  # Go 源代码文件
            exec_file = os.path.join(tmpdirname, "temp")  # 编译后的执行文件

            # 将 Go 代码写入临时源文件
            with open(source_file, 'w') as f:
                f.write(code)

            try:
                # 编译命令
                compile_command = ["go", "build", "-o", exec_file, source_file]
                compile_result = subprocess.run(
                    compile_command,
                    capture_output=True,
                    text=True,
                    timeout=10  # 编译超时设置为 10 秒
                )

                # 如果编译失败，返回编译错误信息
                if compile_result.returncode != 0:
                    return f"编译失败: {compile_result.stderr}"

                # 执行命令
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
                return "错误: 未找到 'go'。请确保已安装 Go 并将其添加到 PATH 中。"
            except Exception as e:
                return f"代码执行失败: {str(e)}"

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
            r"error",  # 错误
            r"failed",  # 失败
            r"traceback",  # 错误堆栈
            r"invalid",  # 无效
            r"exception",  # 异常
            r"syntax",  # 语法错误
            r"panic",  # 崩溃
            r"undefined",  # 未定义
            r"cannot"  # 不能
        ]
        combined_pattern = "|".join(error_patterns)  # 合并所有错误模式为一个正则表达式
        if re.search(combined_pattern, feedback, re.IGNORECASE):  # 如果反馈中包含错误模式
            return True
        return False

if __name__ == "__main__":
    # 示例 Go 代码
    codes = [
"""
package main
import "fmt"

func hello() {
    fmt.Println("Hello, World!")
}
""",
"""
func main() {
    hello()
}
"""
    ]
    g = GoInterpreter()  # 创建 GoInterpreter 实例
    print(g.execute(codes))  # 执行 Go 代码并输出结果
