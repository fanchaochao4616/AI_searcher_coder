import os
import stat
import mimetypes
import configparser

# 导入工具类
if __name__ == "__main__":
    from tools import Tools
else:
    from sources.tools.tools import Tools


class FileFinder(Tools):
    """
    FileFinder 类是一个工具，用于查找当前目录中的文件并返回其信息。
    """

    def __init__(self):
        super().__init__()
        self.tag = "file_finder"  # 设置工具标签为 file_finder

    def read_file(self, file_path: str) -> str:
        """
        读取文件内容。
        参数:
            file_path (str): 要读取的文件路径
        返回:
            str: 文件内容
        """
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except Exception as e:
            return f"读取文件时出错: {e}"

    def get_file_info(self, file_path: str) -> str:
        """
        获取文件的信息，包括文件名、类型、权限和内容。
        参数:
            file_path (str): 文件路径
        返回:
            dict: 文件的详细信息
        """
        if os.path.exists(file_path):
            stats = os.stat(file_path)  # 获取文件的统计信息
            permissions = oct(stat.S_IMODE(stats.st_mode))  # 获取文件权限
            file_type, _ = mimetypes.guess_type(file_path)  # 获取文件类型
            file_type = file_type if file_type else "未知"
            content = self.read_file(file_path)  # 获取文件内容

            result = {
                "filename": os.path.basename(file_path),
                "path": file_path,
                "type": file_type,
                "read": content,
                "permissions": permissions
            }
            return result
        else:
            return {"filename": file_path, "error": "文件未找到"}

    def recursive_search(self, directory_path: str, filename: str) -> str | None:
        """
        在目录及其子目录中递归查找文件。
        参数:
            directory_path (str): 要查找的目录路径
            filename (str): 要查找的文件名
        返回:
            str | None: 如果找到文件，返回文件路径，否则返回 None
        """
        file_path = None
        excluded_files = [".pyc", ".o", ".so", ".a", ".lib", ".dll", ".dylib", ".so", ".git"]  # 排除的文件类型
        for root, dirs, files in os.walk(directory_path):  # 遍历目录及其子目录
            for file in files:
                if any(excluded_file in file for excluded_file in excluded_files):  # 跳过排除的文件
                    continue
                if filename.strip() in file.strip():  # 如果文件名匹配
                    file_path = os.path.join(root, file)
                    return file_path
        return None

    def execute(self, blocks: list, safety: bool = False) -> str:
        """
        执行文件查找操作，查找给定的文件名。
        参数:
            blocks (list): 要查找的文件名列表
        返回:
            str: 文件查找结果
        """
        if not blocks or not isinstance(blocks, list):  # 如果没有提供有效的文件名
            return "错误: 未提供有效的文件名"

        results = []
        for block in blocks:
            filename = block.split(":")[0]  # 提取文件名
            file_path = self.recursive_search(self.current_dir, filename)  # 查找文件
            if file_path is None:
                results.append({"filename": filename, "error": "文件未找到"})
                continue
            if len(block.split(":")) > 1:
                action = block.split(":")[1]  # 获取用户指定的操作
            else:
                action = "info"  # 默认为查看文件信息
            result = self.get_file_info(file_path)  # 获取文件信息
            results.append(result)

        output = ""
        for result in results:
            if "error" in result:
                output += f"文件: {result['filename']} - {result['error']}\n"
            else:
                if action == "read":  # 如果操作是读取文件内容
                    output += result['read']
                else:
                    output += (f"文件: {result['filename']}, "
                               f"路径: {result['path']}, "
                               f"文件类型: {result['type']}\n")
        return output.strip()

    def execution_failure_check(self, output: str) -> bool:
        """
        检查文件查找操作是否失败。
        参数:
            output (str): 来自 execute() 的输出
        返回:
            bool: 如果执行失败，返回 True，否则返回 False
        """
        if not output:
            return True
        if "错误" in output or "未找到" in output:
            return True
        return False

    def interpreter_feedback(self, output: str) -> str:
        """
        提供关于文件查找操作的反馈。
        参数:
            output (str): 来自 execute() 的输出
        返回:
            str: AI 的反馈消息
        """
        if not output:
            return "文件查找工具没有生成输出"

        feedback = "文件查找结果:\n"

        if "错误" in output or "未找到" in output:
            feedback += f"处理失败: {output}\n"
        else:
            feedback += f"成功找到: {output}\n"
        return feedback.strip()


if __name__ == "__main__":
    tool = FileFinder()  # 创建 FileFinder 实例
    result = tool.execute(["toto.txt"], False)  # 查找文件并执行操作
    print("执行结果:")
    print(result)
    print("\n失败检查:", tool.execution_failure_check(result))
    print("\n反馈:")
    print(tool.interpreter_feedback(result))
