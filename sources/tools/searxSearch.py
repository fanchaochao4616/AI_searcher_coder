import os
import requests
from bs4 import BeautifulSoup

# 导入工具类
if __name__ == "__main__":
    from tools import Tools
else:
    from sources.tools.tools import Tools


class searxSearch(Tools):
    """
    searxSearch 类是一个工具，用于查询 SearxNG 实例并提取 URL 和标题。
    """

    def __init__(self, base_url: str = None):
        """
        初始化 SearxSearch 工具，使用 SearxNG 实例的 base URL。
        参数:
            base_url (str): SearxNG 实例的 base URL
        """
        super().__init__()
        self.tag = "web_search"  # 设置工具标签为 web_search
        self.base_url = base_url or os.getenv("SEARXNG_BASE_URL")  # 从环境变量或参数获取 SearxNG base URL
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"  # 用户代理
        self.paywall_keywords = [
            "Member-only", "access denied", "restricted content", "404", "this page is not working"
        ]
        if not self.base_url:
            raise ValueError("SearxNG base URL 必须通过参数或环境变量提供。")

    def link_valid(self, link):
        """
        检查链接是否有效。
        参数:
            link (str): 要检查的 URL 链接
        返回:
            str: 链接的访问状态
        """
        # TODO: 找到更好的方式
        if not link.startswith("http"):
            return "状态: 无效的 URL"

        headers = {"User-Agent": self.user_agent}
        try:
            response = requests.get(link, headers=headers, timeout=5)  # 发送 GET 请求
            status = response.status_code
            if status == 200:
                content = response.text.lower()
                if any(keyword in content for keyword in self.paywall_keywords):
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
        print("正在检查链接的可访问性...")
        for i, link in enumerate(links):
            status = self.link_valid(link)
            statuses.append(status)
        return statuses

    def execute(self, blocks: list, safety: bool = False) -> str:
        """
        执行搜索查询并提取 URL 和标题。
        参数:
            blocks (list): 包含查询字符串的列表
            safety (bool): 是否需要安全确认
        返回:
            str: 查询结果
        """
        if not blocks:
            return "错误: 没有提供查询字符串。"

        query = blocks[0].strip()
        if not query:
            return "错误: 空查询字符串。"

        search_url = f"{self.base_url}/search"
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent
        }
        data = f"q={query}&categories=general&language=auto&time_range=&safesearch=0&theme=simple"
        try:
            response = requests.post(search_url, headers=headers, data=data, verify=False)  # 执行 POST 请求
            response.raise_for_status()  # 如果响应状态不是 200，抛出异常
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            for article in soup.find_all('article', class_='result'):  # 查找所有结果
                url_header = article.find('a', class_='url_header')
                if url_header:
                    url = url_header['href']
                    title = article.find('h3').text.strip() if article.find('h3') else "无标题"
                    description = article.find('p', class_='content').text.strip() if article.find('p',
                                                                                                   class_='content') else "无描述"
                    results.append(f"标题: {title}\n摘要: {description}\n链接: {url}")
            return "\n\n".join(results)  # 返回所有结果，使用换行分隔
        except requests.exceptions.RequestException as e:
            return f"搜索过程中出错: {str(e)}"

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
    search_tool = searxSearch(base_url="http://127.0.0.1:8080")  # 创建 SearxSearch 实例
    result = search_tool.execute(["Are dogs better than cats?"])  # 执行查询
    print(result)  # 输出查询结果
