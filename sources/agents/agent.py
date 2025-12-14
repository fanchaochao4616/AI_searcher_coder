from typing import Tuple, Callable
from abc import abstractmethod
import os
import random
import time

from sources.memory import Memory
from sources.utility import pretty_print

random.seed(time.time())


class executorResult:
    """
    工具执行结果存储类，用于存储每个工具执行的代码块、反馈信息和执行成功与否的状态。
    """

    def __init__(self, blocks, feedback, success):
        self.blocks = blocks  # 存储执行的代码块
        self.feedback = feedback  # 存储执行的反馈信息
        self.success = success  # 存储执行是否成功的状态

    def show(self):
        """
        显示工具执行结果。
        输出代码块和执行反馈信息，根据执行成功与否展示不同颜色。
        """
        for block in self.blocks:
            pretty_print("-" * 100, color="output")  # 打印分隔线
            pretty_print(block, color="code" if self.success else "failure")  # 打印代码块
            pretty_print("-" * 100, color="output")  # 打印分隔线
            pretty_print(self.feedback, color="success" if self.success else "failure")  # 打印反馈信息


class Agent():
    """
    抽象的智能体基类，用于定义智能体的核心功能。
    """

    def __init__(self, model: str,
                 name: str,
                 prompt_path: str,
                 provider,
                 recover_last_session=True) -> None:
        """
        初始化智能体，加载模型、工具、名称、提示词文件和内存。可以选择是否恢复上次会话。
        """
        self.agent_name = name  # 智能体名称
        self.role = None    #智能体角色
        self.current_directory = os.getcwd()  # 当前工作目录
        self.model = model
        self.llm = provider  # LLM 提供者（例如 OpenAI GPT）
        self.memory = Memory(self.load_prompt(prompt_path),
                             recover_last_session=recover_last_session,
                             memory_compression=False)  #智能体的记忆模块，负责存储和管理历史对话记录。
        self.tools = {}  # 存储已注册的工具
        self.blocks_result = []  # 存储工具执行的结果，每个工具执行的结果都会以 executorResult 对象的形式保存。
        self.last_answer = ""  # 存储智能体上一次的回答。

    @property
    def get_memory(self) -> Memory:
        """
        获取智能体的记忆模块。
        """
        return self.memory
    def get_tools(self) -> dict:
        """
        获取所有已注册的工具（工具是外部模块或函数）。
        """
        return self.tools

    def add_tool(self, name: str, tool: Callable) -> None:
        """
        向智能体添加一个带名字的工具。
        确保工具是一个可调用对象（即函数方法）。
        """
        if tool is not Callable:
            raise TypeError("工具必须是可调用对象（方法）")  # 检查工具是否为可调用对象
        self.tools[name] = tool

    def load_prompt(self, file_path: str) -> str:
        """
        加载并读取提示词文件。返回文件的内容作为字符串。
        """
        try:
            with open(file_path, 'r', encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"未找到提示词文件: {file_path}")  # 文件未找到时抛出异常
        except PermissionError:
            raise PermissionError(f"没有权限读取提示词文件: {file_path}")  # 文件权限不足时抛出异常
        except Exception as e:
            raise e

    @abstractmethod
    def process(self, prompt, speech_module) -> str:#speech_module为语音模块
        """
        抽象方法，子类中实现，用于处理输入的提示词并返回智能体的回答。
        """
        pass

    def remove_reasoning_text(self, text: str) -> None:
        """
        移除推理模型的推理部分（例如 deepseek）。
        """
        end_tag = "</think>"
        end_idx = text.rfind(end_tag) + 8
        return text[end_idx:]

    def extract_reasoning_text(self, text: str) -> None:
        """
        提取推理模型的推理部分（例如 deepseek）。
        """
        start_tag = "<think>"
        end_tag = "</think>"
        start_idx = text.find(start_tag)
        end_idx = text.rfind(end_tag) + 8
        return text[start_idx:end_idx]

    def llm_request(self, verbose=False) -> Tuple[str, str]:
        """
        请求 LLM 处理提示词，并返回处理结果（答案和推理过程）。
        """
        memory = self.memory.get()  # 获取内存中的历史对话记录
        thought = self.llm.respond(memory, verbose)  # 通过 LLM 提供者处理请求

        reasoning = self.extract_reasoning_text(thought)  # 提取推理部分
        answer = self.remove_reasoning_text(thought)  # 提取答案部分
        self.memory.push('assistant', answer)  # 将答案推送到内存中
        return answer, reasoning

    def wait_message(self, speech_module):
        """
        如果提供了语音模块，则通过语音模块播放一些等待信息，提示用户稍等。
        """
        if speech_module is None:
            return
        messages = ["请耐心等待，我正在处理。",
                    "计算中... 可以先喝杯咖啡。",
                    "稍等，我正在计算结果。",
                    "正在思考，请稍候。"]
        speech_module.speak(messages[random.randint(0, len(messages) - 1)])  # 随机选择一条消息并通过语音模块输出

    def get_blocks_result(self) -> list:
        """
        获取所有工具执行的结果。
        """
        return self.blocks_result

    def show_answer(self):
        """
        显示智能体的最终答案。
        并展示所有工具执行的结果。会展示代码块及其反馈信息。
        该方法将智能体生成的回答（保存在 `last_answer` 中）按照行进行分割，
        如果某行包含代码块的标识（如 "block:"），则显示该代码块的执行结果。
        其他文本则直接打印出来。执行完成后清空工具执行结果列表。
        """
        lines = self.last_answer.split("\n")    # 将智能体的最后回答按行拆分
        for line in lines:  # 遍历每一行
            if "block:" in line:    # 如果这一行包含代码块的标识（即 "block:"），则处理并显示代码块
                block_idx = int(line.split(":")[1]) # 提取该行标识的代码块索引（从 "block:" 后面的数字）
                if block_idx < len(self.blocks_result): # 确保索引是有效的
                    self.blocks_result[block_idx].show()  # 展示特定的代码块结果
            else:
                pretty_print(line, color="output")  # 打印普通文本
        self.blocks_result = []  #  # 执行完后清空执行结果列表，准备下一次的结果展示

    def remove_blocks(self, text: str) -> str:
        """
        移除回答中的所有代码块，只保留普通文本。可以处理代码块的显示与提取。
        """
        tag = f'```'  #代码块的开始和结束标签（用于标识代码块）
        lines = text.split('\n')    #将输入的文本按行分割
        post_lines = [] #用于存储处理后的文本行
        in_block = False    # 标记当前是否在代码块内
        block_idx = 0   # 用于记录代码块的索引

        # 遍历每一行文本
        for line in lines:
            if tag in line and not in_block:
                # 如果遇到代码块的开始标签，并且当前不在代码块内，进入代码块
                in_block = True
                continue# 跳过当前行，因为它是代码块的开始标签

            if not in_block:
                # 如果当前不在代码块内，直接将当前行添加到处理后的文本中
                post_lines.append(line)

            if tag in line:
                # 如果遇到代码块的结束标签，并且已经进入了代码块，结束代码块
                in_block = False
                post_lines.append(f"block:{block_idx}")  # 记录代码块位置
                block_idx += 1# 增加代码块索引

        # 将处理后的所有行合并为一个字符串并返回
        return "\n".join(post_lines)

    def execute_modules(self, answer: str) -> Tuple[bool, str]:
        """
        执行所有已添加的工具，处理工具返回的结果，并返回是否成功及反馈信息。
        """
        feedback = ""
        success = False
        blocks = None

        for name, tool in self.tools.items():
            feedback = ""
            blocks, save_path = tool.load_exec_block(answer)  # 加载工具的执行块

            if blocks != None:
                pretty_print(f"执行工具: {name}", color="status")  # 打印当前执行工具的名称
                output = tool.execute(blocks)  # 执行工具
                feedback = tool.interpreter_feedback(output)  # 获取工具执行反馈
                success = not tool.execution_failure_check(output)  # 检查执行是否失败
                pretty_print(feedback, color="success" if success else "failure")  # 打印反馈信息
                self.memory.push('user', feedback)  # 将反馈推送到内存
                self.blocks_result.append(executorResult(blocks, feedback, success))  # 保存执行结果
                if not success:
                    return False, feedback  # 如果执行失败，返回失败反馈
                if save_path != None:
                    tool.save_block(blocks, save_path)  # 保存执行块
        return True, feedback  # 返回成功反馈
