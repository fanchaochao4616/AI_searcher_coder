import re
import time

from sources.utility import pretty_print, animate_thinking
from sources.agents.agent import Agent
from sources.tools.searxSearch import searxSearch
from sources.browser import Browser


class BrowserAgent(Agent):
    def __init__(self, model, name, prompt_path, provider):
        """
        BrowserAgent负责根据用户请求自主浏览网页搜索答案。
        """
        super().__init__(model, name, prompt_path, provider)
        self.tools = {
            "web_search": searxSearch(),
        }
        self.role = "深度研究和网络搜索"
        self.browser = Browser()
        self.browser.go_to("https://github.com/")  # 用默认URL（GitHub）启动浏览器
        self.search_history = []  # 存储已访问的搜索结果列表
        self.navigable_links = []  # 存储页面上所有可导航链接的列表
        self.notes = []  # 存储导航或搜索结果中的笔记列表

    def extract_links(self, search_result: str):
        """
        使用正则表达式从搜索结果字符串中提取URL。
        清理并返回链接列表。
        """
        pattern = r'(https?://\S+|www\.\S+)'
        matches = re.findall(pattern, search_result)  # 在文本中查找所有URL
        trailing_punct = ".,!?;:"  # 要删除的标点符号列表
        cleaned_links = [link.rstrip(trailing_punct) for link in matches]  # 从URL中清除尾随标点符号
        return self.clean_links(cleaned_links)  # 进一步清理并返回链接

    def clean_links(self, links: list):
        """
        从链接中删除任何不需要的标点符号或空格。
        """
        links_clean = []
        for link in links:
            link = link.strip()
            if link[-1] == '.':  # 如果存在尾随句号则删除
                links_clean.append(link[:-1])
            else:
                links_clean.append(link)
        return links_clean

    def get_unvisited_links(self):
        """
        返回尚未访问的链接列表。
        """
        return "\n".join(
            [f"[{i}] {link}" for i, link in enumerate(self.navigable_links) if link not in self.search_history])

    def make_newsearch_prompt(self, user_prompt: str, search_result: dict):
        """
        生成提示以指导代理在返回搜索结果后的决策。
        """
        search_choice = self.stringify_search_results(search_result)
        return f"""
        基于搜索结果:
        {search_choice}
        你的目标是找到准确完整的信息来满足用户请求。
        用户请求: {user_prompt}
        要继续，请从搜索结果中选择一个相关链接。通过说"I want to navigate to <link>."来宣布你的选择。
        不要解释你的选择。
        """

    def make_navigation_prompt(self, user_prompt: str, page_text: str):
        """
        为代理创建提示以指导其在网页上的导航决策。
        """
        remaining_links = self.get_unvisited_links()  # 获取尚未访问的剩余链接
        remaini