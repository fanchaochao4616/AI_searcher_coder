import os
import sys
import torch
from transformers import pipeline

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.agents.agent import Agent
from sources.agents.code_agent import CoderAgent
from sources.agents.casual_agent import CasualAgent
from sources.agents.planner_agent import PlannerAgent
from sources.utility import pretty_print


class AgentRouter:
    """
    AgentRouter 类根据用户查询选择合适的代理。
    """

    def __init__(self, agents: list, model_name: str = "facebook/bart-large-mnli"):
        """
        初始化代理路由器，设置模型和代理列表。
        """
        self.model = model_name  # 使用的模型
        self.pipeline = pipeline("zero-shot-classification", model=self.model)  # 使用零样本分类
        self.agents = agents  # 代理列表
        self.labels = [agent.role for agent in agents]  # 获取所有代理的角色标签

    def get_device(self) -> str:
        """
        获取可用的计算设备，优先使用 GPU。
        """
        if torch.cuda.is_available():
            return "cuda:0"
        else:
            return "cpu"

    def classify_text(self, text: str, threshold: float = 0.5) -> list:
        """
        将文本分类到不同的标签（代理角色）。
        参数:
            text (str): 要分类的文本
            threshold (float, optional): 分类的阈值，默认值为 0.5
        返回:
            list: 代理和它们的分数列表
        """
        first_sentence = None
        for line in text.split("\n"):  # 获取文本的第一行
            first_sentence = line.strip()
            break
        if first_sentence is None:
            first_sentence = text  # 如果没有第一行，则直接使用整个文本
        result = self.pipeline(first_sentence, self.labels, threshold=threshold)  # 使用模型进行分类
        return result

    def select_agent(self, text: str) -> Agent:
        """
        根据文本选择合适的代理。
        参数:
            text (str): 用于选择代理的文本
        返回:
            Agent: 选中的代理
        """
        if len(self.agents) == 0 or len(self.labels) == 0:  # 如果没有代理，返回第一个代理
            return self.agents[0]
        result = self.classify_text(text)  # 获取文本分类结果
        for agent in self.agents:  # 遍历所有代理，选择匹配的代理
            if result["labels"][0] == agent.role:
                pretty_print(f"选择了代理: {agent.agent_name}", color="warning")  # 打印选中的代理
                return agent
        return None  # 如果没有匹配的代理，返回 None


if __name__ == "__main__":
    # 初始化代理列表
    agents = [
        CoderAgent("deepseek-r1:14b", "agent1", "../prompts/coder_agent.txt", "server"),
        CasualAgent("deepseek-r1:14b", "agent2", "../prompts/casual_agent.txt", "server"),
        PlannerAgent("deepseek-r1:14b", "agent3", "../prompts/planner_agent.txt", "server")
    ]

    # 创建 AgentRouter 实例
    router = AgentRouter(agents)

    # 示例文本，模拟不同类型的任务
    texts = ["""
    编写一个 Python 脚本来检查我网络上的设备是否连接到互联网
    """,
             """
             嘿，你能帮我在网上搜索一下关于股市的最新新闻吗？
             """,
             """
             嘿，你能给我列出当前目录中的文件吗？
             """,
             """
             做一个有趣的游戏，来展示当前美国和欧洲之间的关系
             """
             ]

    # 对每个文本进行分类，并选择合适的代理
    for text in texts:
        print(text)
        results = router.classify_text(text)  # 获取文本的分类结果
        for result in results:
            print(result["label"], "=>", result["score"])  # 打印分类标签及其分数
        agent = router.select_agent(text)  # 根据文本选择代理
        print("选择的代理角色:", agent.role)  # 打印选中的代理角色
