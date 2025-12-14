from sources.utility import pretty_print, animate_thinking
from sources.agents.agent import Agent
from sources.tools.fileFinder import FileFinder
from sources.tools.BashInterpreter import BashInterpreter


class FileAgent(Agent):
    def __init__(self, model, name, prompt_path, provider):
        """
        FileAgent 是一个专门处理文件操作的代理。
        该代理能够执行与文件相关的操作，如查找文件、执行Bash命令等。
        """
        super().__init__(model, name, prompt_path, provider)

        # 定义 FileAgent 可以使用的工具
        self.tools = {
            "file_finder": FileFinder(),  # 用于查找文件
            "bash": BashInterpreter()  # 用于执行 Bash 命令
        }

        self.role = "文件操作"  # 设置代理角色为文件操作

    def process(self, prompt, speech_module) -> str:
        """
        处理用户的输入，执行文件相关的操作并返回结果。
        如果执行成功，结束操作；如果失败，继续尝试。
        """
        complete = False
        exec_success = False
        self.memory.push('user', prompt)  # 将用户输入存入记忆中

        self.wait_message(speech_module)  # 等待消息
        while not complete:
            if exec_success:  # 如果执行成功，结束循环
                complete = True
            animate_thinking("思考中...", color="status")  # 显示思考中的动画
            answer, reasoning = self.llm_request()  # 从模型获取回答
            exec_success, _ = self.execute_modules(answer)  # 执行可能包含的代码模块
            answer = self.remove_blocks(answer)  # 移除回答中的代码块
            self.last_answer = answer
            complete = True  # 默认完成任务
            # 如果找到可执行的代码块，继续执行任务
            for name, tool in self.tools.items():
                if tool.found_executable_blocks():
                    complete = False  # 如果找到可执行块，继续对话
        return answer, reasoning  # 返回最终的回答和推理过程


if __name__ == "__main__":
    from llm_provider import Provider

    # 本地提供者（如果需要可以启用）
    # local_provider = Provider("ollama", "deepseek-r1:14b", None)

    # 设置基于服务器的提供者
    server_provider = Provider("server", "deepseek-r1:14b", "192.168.1.100:5000")

    # 创建 FileAgent 实例，提供模型、名称、提示路径和提供者
    agent = FileAgent("deepseek-r1:14b", "jarvis", "prompts/file_agent.txt", server_provider)

    # 处理用户输入的问题，查询文件内容
    ans = agent.process("What is the content of the file toto.py ?")

    # 输出答案
    print(ans)
