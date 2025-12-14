import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import time
import datetime
import uuid
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.utility import timer_decorator


class Memory():
    """
    Memory 类用于管理对话的记忆。
    提供了一个方法来压缩记忆。
    """

    def __init__(self, system_prompt: str,
                 recover_last_session: bool = False,
                 memory_compression: bool = True):
        self.memory = []
        self.memory = [{'role': 'user', 'content': system_prompt}]  # 初始化记忆，加入系统提示

        self.session_time = datetime.datetime.now()  # 会话开始时间
        self.session_id = str(uuid.uuid4())  # 会话ID，使用UUID生成
        self.conversation_folder = f"conversations/"  # 存储对话的文件夹路径
        if recover_last_session:
            self.load_memory()  # 恢复上次会话
        # 启用记忆压缩系统
        self.model = "pszemraj/led-base-book-summary"  # 使用预训练的摘要模型
        self.device = self.get_cuda_device()  # 获取设备类型（CPU, CUDA, MPS）
        self.memory_compression = memory_compression  # 是否启用记忆压缩
        if memory_compression:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model)  # 加载分词器
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model)  # 加载模型

    def get_filename(self) -> str:
        """根据会话时间生成文件名"""
        return f"memory_{self.session_time.strftime('%Y-%m-%d_%H-%M-%S')}.txt"

    def save_memory(self) -> None:
        """将当前会话的记忆保存到文件中"""
        if not os.path.exists(self.conversation_folder):  # 如果文件夹不存在，则创建
            os.makedirs(self.conversation_folder)
        filename = self.get_filename()  # 获取文件名
        path = os.path.join(self.conversation_folder, filename)  # 完整路径
        json_memory = json.dumps(self.memory)  # 将记忆转为JSON格式
        with open(path, 'w') as f:
            f.write(json_memory)  # 写入文件

    def find_last_session_path(self) -> str:
        """查找最后一个会话文件路径"""
        saved_sessions = []
        for filename in os.listdir(self.conversation_folder):  # 遍历文件夹
            if filename.startswith('memory_'):  # 如果是会话文件
                date = filename.split('_')[1]
                saved_sessions.append((filename, date))
        saved_sessions.sort(key=lambda x: x[1], reverse=True)  # 按日期排序
        if len(saved_sessions) > 0:
            return saved_sessions[0][0]  # 返回最新的文件名
        return None

    def load_memory(self) -> None:
        """加载上次会话的记忆"""
        if not os.path.exists(self.conversation_folder):  # 如果文件夹不存在
            return
        filename = self.find_last_session_path()  # 获取最后的会话文件
        if filename is None:  # 如果没有找到会话文件
            return
        path = os.path.join(self.conversation_folder, filename)  # 完整路径
        with open(path, 'r') as f:
            self.memory = json.load(f)  # 从文件中加载记忆

    def reset(self, memory: list) -> None:
        """重置记忆为新的列表"""
        self.memory = memory

    def push(self, role: str, content: str) -> None:
        """将消息推送到记忆中"""
        self.memory.append({'role': role, 'content': content})
        # 实验性功能：如果启用记忆压缩，并且角色是助手（assistant），则进行压缩
        if self.memory_compression and role == 'assistant':
            self.compress()

    def clear(self) -> None:
        """清空记忆"""
        self.memory = []

    def get(self) -> list:
        """获取当前记忆"""
        return self.memory

    def get_cuda_device(self) -> str:
        """返回设备类型，优先使用CUDA或MPS"""
        if torch.backends.mps.is_available():
            return "mps"  # 如果支持MPS（MacOS的GPU加速）
        elif torch.cuda.is_available():
            return "cuda"  # 如果支持CUDA
        else:
            return "cpu"  # 默认使用CPU

    def summarize(self, text: str, min_length: int = 64) -> str:
        """
        使用AI模型对文本进行总结。
        参数:
            text (str): 要总结的文本
            min_length (int, optional): 总结的最小长度，默认为64。
        返回:
            str: 总结后的文本
        """
        if self.tokenizer is None or self.model is None:  # 如果没有加载模型或分词器
            return text
        max_length = len(text) // 2 if len(text) > min_length * 2 else min_length * 2
        input_text = "summarize: " + text  # 向模型提供总结指令
        inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)  # 编码输入文本
        summary_ids = self.model.generate(
            inputs['input_ids'],
            max_length=max_length,  # 总结的最大长度
            min_length=min_length,  # 总结的最小长度
            length_penalty=1.0,  # 长度惩罚，用于调整总结的长度
            num_beams=4,  # 使用束搜索以提高质量
            early_stopping=True  # 一旦所有束完成，停止生成
        )
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)  # 解码总结结果
        summary.replace('summary:', '')  # 移除不必要的"summary:"前缀
        return summary

    @timer_decorator
    def compress(self) -> str:
        """
        使用AI模型压缩记忆。
        """
        if not self.memory_compression:  # 如果不启用记忆压缩
            return
        for i in range(len(self.memory)):
            if i <= 2:  # 跳过前3条消息
                continue
            if self.memory[i]['role'] == 'assistant':  # 如果角色是助手，则对内容进行总结
                self.memory[i]['content'] = self.summarize(self.memory[i]['content'])


if __name__ == "__main__":
    # 初始化记忆类，传入系统提示语
    memory = Memory("You are a helpful assistant.",
                    recover_last_session=False, memory_compression=True)

    # 测试推送和压缩功能
    sample_text = """
    The error you're encountering:
    cuda.cu:52:10: fatal error: helper_functions.h: No such file or directory
     #include <helper_functions.h>
    indicates that the compiler cannot find the helper_functions.h file. This is because the #include <helper_functions.h> directive is looking for the file in the system's include paths, but the file is either not in those paths or is located in a different directory.
    1. Use #include "helper_functions.h" Instead of #include <helper_functions.h>
    Angle brackets (< >) are used for system or standard library headers.
    Quotes (" ") are used for local or project-specific headers.
    If helper_functions.h is in the same directory as cuda.cu, change the include directive to:
    3. Verify the File Exists
    Double-check that helper_functions.h exists in the specified location. If the file is missing, you'll need to obtain or recreate it.
    4. Use the Correct CUDA Samples Path (if applicable)
    If helper_functions.h is part of the CUDA Samples, ensure you have the CUDA Samples installed and include the correct path. For example, on Linux, the CUDA Samples are typically located in /usr/local/cuda/samples/common/inc. You can include this path like so:
    Use #include "helper_functions.h" for local files.
    Use the -I flag to specify the directory containing helper_functions.h.
    Ensure the file exists in the specified location.
    """

    memory.push('user', "why do i get this error?")
    memory.push('assistant', sample_text)
    print("\n---\nmemory before:", memory.get())
    memory.compress()  # 执行记忆压缩
    print("\n---\nmemory after:", memory.get())
    memory.save_memory()  # 保存记忆
