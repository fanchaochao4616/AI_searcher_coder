import json
from sources.utility import pretty_print, animate_thinking
from sources.agents.agent import Agent
from sources.agents.code_agent import CoderAgent
from sources.agents.file_agent import FileAgent
from sources.agents.casual_agent import CasualAgent
from sources.tools.tools import Tools


class PlannerAgent(Agent):
    def __init__(self, model, name, prompt_path, provider):
        """
        PlannerAgent 是一个专门的代理，负责将复杂任务分解并逐一解决。
        """
        super().__init__(model, name, prompt_path, provider)

        # 定义PlannerAgent可用的工具，当前只有一个工具是JSON解析器
        self.tools = {
            "json": Tools()
        }
        self.tools['json'].tag = "json"  # 设置json工具的标签

        # 定义三个子代理：编码器、文件操作、网页搜索
        self.agents = {
            "coder": CoderAgent(model, name, prompt_path, provider),  # 编码相关任务
            "file": FileAgent(model, name, prompt_path, provider),  # 文件操作相关任务
            "web": CasualAgent(model, name, prompt_path, provider)  # 闲聊和网页搜索相关任务
        }
        self.role = "复杂编程任务和网页研究"  # 设置角色
        self.tag = "json"  # 设置标签为json

    def parse_agent_tasks(self, text):
        """
        解析传入的文本，提取任务及其对应的代理信息。
        """
        tasks = []  # 存储任务
        tasks_names = []  # 存储任务名称

        # 按行拆分文本
        lines = text.strip().split('\n')
        for line in lines:
            if line is None or len(line) == 0:  # 跳过空行
                continue
            line = line.strip()
            if '##' in line or line[0].isdigit():  # 如果是标题或编号，认为是任务名称
                tasks_names.append(line)
                continue

        # 解析JSON块
        blocks, _ = self.tools["json"].load_exec_block(text)
        if blocks == None:
            return (None, None)

        # 从JSON中提取任务和代理信息
        for block in blocks:
            line_json = json.loads(block)
            if 'plan' in line_json:  # 如果JSON中有计划字段
                for task in line_json['plan']:
                    agent = {
                        'agent': task['agent'],
                        'id': task['id'],
                        'task': task['task']
                    }
                    if 'need' in task:  # 如果任务中有需求信息
                        agent['need'] = task['need']
                    tasks.append(agent)

        # 如果任务名称和任务数不匹配，返回任务名称和任务对的zip
        if len(tasks_names) != len(tasks):
            names = [task['task'] for task in tasks]
            return zip(names, tasks)

        return zip(tasks_names, tasks)

    def make_prompt(self, task, needed_infos):
        """
        根据任务和所需信息生成一个新的提示语句。
        """
        prompt = f"""
        你获得了以下信息：
        {needed_infos}
        你的任务是：
        {task}
        """
        return prompt

    def process(self, prompt, speech_module) -> str:
        """
        处理用户输入的任务，并将任务分配给相应的代理。
        """
        self.memory.push('user', prompt)  # 将用户输入存入记忆中
        self.wait_message(speech_module)  # 等待消息
        animate_thinking("思考中...", color="status")  # 显示思考中的动画
        agents_tasks = (None, None)
        answer, reasoning = self.llm_request()  # 从LLM获取回答
        agents_tasks = self.parse_agent_tasks(answer)  # 解析任务

        if agents_tasks == (None, None):  # 如果没有成功解析任务，返回错误信息
            return "无法解析任务", reasoning

        # 遍历任务并为每个任务分配相应的代理
        for task_name, task in agents_tasks:
            pretty_print(f"我将 {task_name}。", color="info")  # 打印当前任务名称
            agent_prompt = self.make_prompt(task['task'], task['need'])  # 为每个任务生成提示
            pretty_print(f"分配代理 {task['agent']} 给任务 {task_name}", color="info")  # 打印任务分配信息
            speech_module.speak(f"我将 {task_name}。我已将任务分配给 {task['agent']} 代理。")  # 向用户说出任务分配信息

            try:
                # 执行代理任务
                self.agents[task['agent'].lower()].process(agent_prompt, None)
                pretty_print(f"-- 代理回答 ---\n\n", color="output")
                self.agents[task['agent'].lower()].show_answer()  # 显示代理的回答
                pretty_print(f"\n\n", color="output")
            except Exception as e:
                pretty_print(f"错误: {e}", color="failure")  # 如果执行过程中发生错误，打印错误信息
                speech_module.speak(f"我遇到一个错误: {e}")  # 向用户说出错误信息
                break

        self.last_answer = answer  # 更新最后的回答
        return answer, reasoning  # 返回最终的回答和推理过程


if __name__ == "__main__":
    from llm_provider import Provider

    # 本地提供者（如果需要可以启用）
    # local_provider = Provider("ollama", "deepseek-r1:14b", None)

    # 设置基于服务器的提供者
    server_provider = Provider("server", "deepseek-r1:14b", "192.168.1.100:5000")

    # 创建 PlannerAgent 实例，提供模型、名称、提示路径和提供者
    agent = PlannerAgent("deepseek-r1:14b", "jarvis", "prompts/planner_agent.txt", server_provider)

    # 处理用户输入的问题，规划任务
    ans = agent.process("Make a cool game to illustrate the current relation between USA and Europe")

    # 输出答案
    print(ans)
