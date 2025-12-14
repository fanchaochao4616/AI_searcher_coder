import os
import requests
import dotenv

dotenv.load_dotenv()

# 导入工具类
if __name__ == "__main__":
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utility import animate_thinking, pretty_print
    from tools import Tools
else:
    from sources.tools.tools import Tools
    from sources.utility import animate_thinking, pretty_print

"""
警告
webSearch 已完全弃用，正在由 searxSearch 替代用于网页搜索。
"""


class webSearch(Tools):
    """
    webSearch 类是一个工具，用于执行 Google 搜索并返回第一个结果的信息。
    """

    def __init__(self, api_key: str = None):
        """
        初始化 webSearch 工具，使用 SerpApi API 执行网页搜索。
        参数:
            api_key (str): SerpApi 的 API 密钥
        """
        super().__init__()
        self.tag = "web_search"  # 设置工具标签为 web_search
        self.api_key = api_key or os.getenv("SERPAPI_KEY")  # 如果没有传入 API 密钥，尝试从环境变量获取
        self.paywall_keywords = [
            "subscribe", "login to continue", "access denied", "restricted content", "404", "this page is not working"
        ]  # 付费墙关键词

    def link_valid(self, link):
        """
        检查链接是否有效。
        参数:
            link (str): 要检查的 URL 链接
        返回:
            str: 链接的访问状态
        """
        # 检查链接是否以 http 开头
        if not link.startswith("http"):
            return "状态: 无效的 URL"

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            response = requests.get(link, headers=headers, timeout=5)  # 发送 GET 请求
            status = response.status_code
            if status == 200:
                content = response.text[:1000].lower()
                if any(keyword in content for keyword in self.paywall_keywords):  # 检查是否有付费墙关键词
                    return "状态: 可能是付费墙"
                return "状态: 可访问"
            elif status == 404:
                return "状态: 404 未找到"
            elif status == 403:
                return "状态: 403 禁止访问"
            else:
                return f"状态: {status} {response.reason}"
        except requests.exceptions.RequestException as e:
            return f"错误: {str(e)}"

    def check_all_links(self, links):
        """
        检查所有链接的有效性。
        参数:
            links (list): 链接列表
        返回:
            list: 每个链接的访问状态
        """
        # TODO: 使其异步执行
        statuses = []
        print("开始扫描网页并检查链接的可访问性...")
        for i, link in enumerate(links):
            status = self.link_valid(link)
            statuses.append(status)
        return statuses

    def execute(self, blocks: str, safety: bool = True) -> str:
        """
        执行搜索查询并提取 URL 和标题。
        参数:
            blocks (list): 包含查询字符串的列表
            safety (bool): 是否需要安全确认
        返回:
            str: 查询结果
        """
        if self.api_key is None:
            return "错误: 没有提供 SerpApi API 密钥。"

        for block in blocks:
            query = block.strip()
            pretty_print(f"正在搜索: {query}", color="status")
            if not query:
                return "错误: 没有提供查询字符串。"

            try:
                url = "https://serpapi.com/search"
                params = {
                    "q": query,
                    "api_key": self.api_key,
                    "num": 50,
                    "output": "json"
                }
                response = requests.get(url, params=params)  # 执行 GET 请求
                response.raise_for_status()  # 如果响应状态不是 200，抛出异常

                data = response.json()
                results = []
                if "organic_results" in data and len(data["organic_results"]) > 0:
                    organic_results = data["organic_results"][:50]  # 只取前 50 个结果
                    links = [result.get("link", "无链接") for result in organic_results]
                    statuses = self.check_all_links(links)  # 检查所有链接的状态
                    for result, status in zip(organic_results, statuses):
                        if not "OK" in status:
                            continue
                        title = result.get("title", "无标题")
                        snippet = result.get("snippet", "无描述")
                        link = result.get("link", "无链接")
                        results.append(f"标题:{title}\n摘要:{snippet}\n链接:{link}")
                    return "\n\n".join(results)  # 返回查询结果
                else:
                    return "未找到查询结果。"
            except requests.exceptions.RequestException as e:
                return f"搜索过程中出错: {str(e)}"
            except Exception as e:
                return f"发生意外错误: {str(e)}"
        return "没有执行搜索"

    def execution_failure_check(self, output: str) -> bool:
        """
        检查执行是否失败。
        参数:
            output (str): 执行结果
        返回:
            bool: 如果执行失败，返回 True，否则返回 False
        """
        return "错误" in output

    def interpreter_feedback(self, output: str) -> str:
        """
        为代理提供搜索反馈。
        参数:
            output (str): 搜索结果
        返回:
            str: 搜索反馈消息
        """
        if self.execution_failure_check(output):  # 如果搜索失败，返回错误反馈
            return f"网页搜索失败: {output}"
        return f"网页搜索结果:\n{output}"  # 返回搜索结果


if __name__ == "__main__":
    search_tool = webSearch(api_key=os.getenv("SERPAPI_KEY"))  # 创建 webSearch 实例
    query = "when did covid start"  # 设置查询字符串
    result = search_tool.execute([query], safety=True)  # 执行查询
    output = search_tool.interpreter_feedback(result)  # 获取反馈
    print(output)  # 输出搜索结果
