"""
定义一个通用工具类，任何工具都可以由代理使用。

工具可以像下面这样被deepseek使用：
```<工具名称>
<执行的代码或查询>
```

例如:
```python
print("Hello world")
```
此代码将由工具执行，并使用该工具自己的类实现来执行。
工具不仅可以是代码工具，还可以是API、互联网等。
"""

import sys
import os
import configparser
from abc import abstractmethod

sys.path.append('..')

class Tools():
    """
    所有工具的抽象类。.
    """
    def __init__(self):
        self.tag = "undefined"# 工具的标记，默认值为undefined
        self.api_key = None# API密钥，默认值为空
        self.client = None# 客户端对象，默认值为空
        self.messages = []# 存储消息的列表
        self.config = configparser.ConfigParser()# 配置文件读取器
        self.current_dir = self.create_work_dir()# 当前工作目录
        self.excutable_blocks_found = False# 是否找到可执行代码块

    def check_config_dir_validity(self):
        """
        检查配置目录的有效性。
        """
        path = self.config['MAIN']['work_dir']
        if path == "":
            print("警告: 配置文件中未设置工作目录")
            return False
        if path.lower() == "none":
            print("警告: 配置文件中设置的工作目录为 none")
            return False
        if not os.path.exists(path):
            print(f"警告: 工作目录 {path} 不存在")
            return False
        return True

    def config_exists(self):
        """
        检查配置文件是否存在。
        """
        return os.path.exists('./config.ini')

    def create_work_dir(self):
        """
        如果工作目录不存在，则创建工作目录。
        """
        default_path = os.path.dirname(os.getcwd())  # 默认路径为当前工作目录
        if self.config_exists():
            self.config.read('./config.ini')
            config_path = self.config['MAIN']['work_dir']
            dir_path = default_path if not self.check_config_dir_validity() else config_path
        else:
            dir_path = default_path
        return dir_path

    @abstractmethod
    def execute(self, blocks: [str], safety: bool) -> str:
        """
        子类必须实现的抽象方法，用于执行工具的功能。
        参数：
            blocks (List[str]): 要执行的代码或查询块
            safety (bool): 是否需要人工干预
        返回：
            str: 执行工具后的输出结果
        """
        pass

    @abstractmethod
    def execution_failure_check(self, output: str) -> bool:
        """
        子类必须实现的抽象方法，用于检查工具执行是否失败。
        参数：
            output (str): 工具执行后的输出结果
        返回：
            bool: 如果执行失败返回True，否则返回False
        """
        pass

    @abstractmethod
    def interpreter_feedback(self, output: str) -> str:
        """
        子类必须实现的抽象方法，用于根据工具的输出结果提供反馈。
        参数：
            output (str): 工具执行后的输出结果
        返回：
            str: AI的反馈消息
        """
        pass

    def save_block(self, blocks: [str], save_path: str) -> None:
        """
        将代码或查询块保存到指定路径的文件中。
        如果目录不存在，则创建目录路径。
        参数：
            blocks (List[str]): 要保存的代码/查询块列表
            save_path (str): 保存的文件路径
        """
        if save_path is None:
            return
        save_path_dir = os.path.dirname(save_path)
        save_path_file = os.path.basename(save_path)
        directory = os.path.join(self.current_dir, save_path_dir)
        if directory and not os.path.exists(directory):
            print(f"创建目录: {directory}")
            os.makedirs(directory)
        for block in blocks:
            print(f"将代码块保存到: {save_path}")
            with open(os.path.join(directory, save_path_file), 'w') as f:
                f.write(block)

    def found_executable_blocks(self):
        """
        检查是否找到可执行的代码块。
        """
        tmp = self.excutable_blocks_found
        self.excutable_blocks_found = False
        return tmp

    def load_exec_block(self, llm_text: str) -> tuple[list[str], str | None]:
        """
        从LLM生成的文本中提取代码/查询块，并处理它们以便执行。
        该方法解析文本，查找标记为工具标签的代码块（例如 ```python）。
        参数：
            llm_text (str): 包含LLM生成的代码块的原始文本
        返回：
            tuple[list[str], str | None]: 一个包含以下内容的元组：
                - 提取并处理后的代码块列表
                - 保存代码块的路径（如果存在）
        """
        assert self.tag != "undefined", "标签未定义"
        start_tag = f'```{self.tag}'  # 起始标签
        end_tag = '```'  # 结束标签
        code_blocks = []  # 存储代码块的列表
        start_index = 0
        save_path = None

        if start_tag not in llm_text:
            return None, None

        while True:
            start_pos = llm_text.find(start_tag, start_index)
            if start_pos == -1:
                break

            line_start = llm_text.rfind('\n', 0, start_pos) + 1
            if line_start == 0:
                line_start = 0
            leading_whitespace = llm_text[line_start:start_pos]

            end_pos = llm_text.find(end_tag, start_pos + len(start_tag))
            if end_pos == -1:
                break
            content = llm_text[start_pos + len(start_tag):end_pos]
            lines = content.split('\n')
            if leading_whitespace:
                processed_lines = []
                for line in lines:
                    if line.startswith(leading_whitespace):
                        processed_lines.append(line[len(leading_whitespace):])
                    else:
                        processed_lines.append(line)
                content = '\n'.join(processed_lines)

            if ':' in content.split('\n')[0]:
                save_path = content.split('\n')[0].split(':')[1]
                content = content[content.find('\n') + 1:]
            self.excutable_blocks_found = True
            code_blocks.append(content)
            start_index = end_pos + len(end_tag)
        return code_blocks, save_path


if __name__ == "__main__":
    tool = Tools()
    tool.tag = "python"# 设置工具的标签为python
    rt = tool.load_exec_block("""
明白了，让我展示一下当前目录下的Python文件：

```python
import os

for file in os.listdir():
    if file.endswith('.py'):
        print(file)
```
    """)
    print(rt) # 输出提取的代码块和保存路径