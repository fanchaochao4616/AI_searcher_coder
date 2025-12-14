from sources.utility import pretty_print, animate_thinking
from sources.agents.agent import Agent, executorResult
from sources.tools.C_Interpreter import CInterpreter
from sources.tools.GoInterpreter import GoInterpreter
from sources.tools.PyInterpreter import PyInterpreter
from sources.tools.BashInterpreter import BashInterpreter
from sources.tools.fileFinder import FileFinder


class CoderAgent(Agent):
    """
    CoderAgent 是一个可以编写和执行代码的代理。
    它支持多种编程语言的执行，如 Bash、Python、C 和 Go 等。
    """

    def __init__(self, model, name, prompt_path, provider):
        super().__init__(model, name, prompt_path, provider)

        # 定义代理可以使用的工具
        self.tools = {
            "bash": BashInterpreter(),  # 用于执行 Bash 命令
            "python": PyInterpreter(),  # 用于执行 Python 代码
            "c": CInterpreter(),  # 用于执行 C 语言代码
            "go": GoInterpreter(),  # 用于执行 Go 语言代码
            "file_finder": FileFinder()  # 用于查找文件
        }

        self.role = "coding and programming"  # 设置代理角色为编程和代码执行

    def process(self, prompt, speech_module) -> str:
        """
        处理用户的输入，执行代码并返回结果。
        如果代码执行失败，最多重试三次。
        """
        answer = ""
        attempt = 0
        max_attempts = 3  # 最大重试次数
        self.memory.push('user', prompt)  # 将用户输入存入记忆中

        while attempt < max_attempts:
            animate_thinking("思考中...", color="status")  # 显示思考中的动画
            self.wait_message(speech_module)  # 等待消息
            answer, reasoning = self.llm_request()  # 从模型获取回答
            animate_thinking("正在执行代码...", color="status")  # 显示执行代码的动画
            exec_success, _ = self.execute_modules(answer)  # 执行可能包含的代码模块
            answer = self.remove_blocks(answer)  # 移除回答中的代码块
            self.last_answer = answer
            if exec_success:  # 如果执行成功，跳出循环
                break
            self.show_answer()  # 显示当前的回答
            attempt += 1  # 增加尝试次数

        if attempt == max_attempts:  # 如果达到最大重试次数，返回错误提示
            return "抱歉，我没有找到解决方案。你希望我如何继续？", reasoning

        return answer, reasoning  # 返回最终的答案和推理过程


if __name__ == "__main__":
    from llm_provider import Provider

    # 本地提供者（如果需要可以启用）
    # local_provider = Provider("ollama", "deepseek-r1:14b", None)

    # 设置基于服务器的提供者
    server_provider = Provider("server", "deepseek-r1:14b", "192.168.1.100:5000")

    # 创建 CoderAgent 实例，提供模型、名称、提示路径和提供者
    agent = CoderAgent("deepseek-r1:14b", "jarvis", "prompts/coder_agent.txt", server_provider)

    # 处理一个示例问题：计算 5+5 的结果
    ans = agent.process("What is the output of 5+5 in python ?")

    # 输出答案
    print(ans)
