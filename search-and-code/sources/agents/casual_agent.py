from sources.utility import pretty_print, animate_thinking
from sources.agents.agent import Agent
from sources.tools.searxSearch import searxSearch
from sources.tools.flightSearch import FlightSearch
from sources.tools.fileFinder import FileFinder
from sources.tools.BashInterpreter import BashInterpreter


class CasualAgent(Agent):
    def __init__(self, model, name, prompt_path, provider):
        """
        CasualAgent 是一个专门与用户进行闲聊的代理，不执行特定任务。
        """
        super().__init__(model, name, prompt_path, provider)

        # 定义 CasualAgent 可以使用的工具
        self.tools = {
            "web_search": searxSearch(),  # 用于网页搜索
            "flight_search": FlightSearch(),  # 用于航班搜索
            "file_finder": FileFinder(),  # 用于文件查找
            "bash": BashInterpreter()  # 用于执行Bash命令
        }

        self.role = "casual talking"  # 设置代理的角色为闲聊

    def process(self, prompt, speech_module) -> str:
        """
        处理用户的输入，并根据输入生成响应。
        如果回答中包含可执行模块，代理将继续进行对话。
        """
        complete = False
        self.memory.push('user', prompt)  # 将用户输入存入记忆中

        self.wait_message(speech_module)  # 等待消息，如果需要
        while not complete:
            animate_thinking("思考中...", color="status")  # 显示思考中状态
            answer, reasoning = self.llm_request()  # 从模型获取回答
            exec_success, _ = self.execute_modules(answer)  # 执行回答中可能包含的模块
            answer = self.remove_blocks(answer)  # 清理回答中的代码块
            self.last_answer = answer
            complete = True  # 假设对话已完成，除非找到更多任务需要处理
            # 检查是否有工具需要继续执行
            for tool in self.tools.values():
                if tool.found_executable_blocks():
                    complete = False  # 如果找到可执行块，继续对话
        return answer, reasoning  # 返回回答和推理过程


if __name__ == "__main__":
    from llm_provider import Provider

    # 本地提供者（如果需要可以启用）
    # local_provider = Provider("ollama", "deepseek-r1:14b", None)

    # 设置基于服务器的提供者
    server_provider = Provider("server", "deepseek-r1:14b", "192.168.1.100:5000")

    # 创建 CasualAgent 实例，提供模型、名称、提示路径和提供者
    agent = CasualAgent("deepseek-r1:14b", "jarvis", "prompts/casual_agent.txt", server_provider)

    # 处理用户的输入，进行闲聊
    ans = agent.process("你好，你怎么样？")

    # 输出回答
    print(ans)
