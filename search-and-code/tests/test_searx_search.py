import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # 将项目根目录添加到Python路径中
from sources.tools.searxSearch import searxSearch
from dotenv import load_dotenv
import requests  # 导入requests模块用于发送HTTP请求

load_dotenv()  # 加载环境变量

class TestSearxSearch(unittest.TestCase):

    def setUp(self):
        """
        设置每个测试用例的环境，在每个测试前执行。
        """
        os.environ['SEARXNG_BASE_URL'] = "http://127.0.0.1:8080"  # 设置环境变量为默认的SearxNG服务地址
        self.base_url = os.getenv("SEARXNG_BASE_URL")  # 获取环境变量中的SearxNG基础URL
        self.search_tool = searxSearch(base_url=self.base_url)  # 初始化SearxSearch工具
        self.valid_query = "test query"  # 定义一个有效的查询
        self.invalid_query = ""  # 定义一个无效的查询

    def test_initialization_with_env_variable(self):
        """
        测试使用环境变量初始化工具。
        """
        # 临时修改环境变量以测试不同的URL
        os.environ['SEARXNG_BASE_URL'] = "http://test.example.com"
        search_tool = searxSearch()  # 使用新的环境变量初始化工具
        self.assertEqual(search_tool.base_url, "http://test.example.com")  # 确认是否使用了正确的URL
        del os.environ['SEARXNG_BASE_URL']  # 恢复环境变量

    def test_initialization_no_base_url(self):
        """
        测试如果没有提供基础URL，工具是否会抛出错误。
        """
        if 'SEARXNG_BASE_URL' in os.environ:
            del os.environ['SEARXNG_BASE_URL']  # 删除环境变量，确保没有基础URL
        with self.assertRaises(ValueError):  # 确保抛出ValueError
            searxSearch(base_url=None)  # 初始化时没有提供基础URL
        # 恢复环境变量
        os.environ['SEARXNG_BASE_URL'] = "http://searx.lan"

    def test_execute_valid_query(self):
        """
        测试执行有效查询时返回结果。
        """
        result = self.search_tool.execute([self.valid_query])  # 执行有效查询
        print(f"Output from test_execute_valid_query: {result}")
        self.assertTrue(isinstance(result, str), "Result should be a string.")  # 确保返回的是字符串
        self.assertNotEqual(result, "", "Result should not be empty. Check SearxNG instance.")  # 确保返回的结果不为空

    def test_execute_empty_query(self):
        """
        测试执行空查询时的处理。
        """
        result = self.search_tool.execute([""])  # 执行空查询
        print(f"Output from test_execute_empty_query: {result}")
        self.assertEqual(result, "Error: Empty search query provided.")  # 确认返回错误消息

    def test_execute_no_query(self):
        """
        测试没有查询时的处理。
        """
        result = self.search_tool.execute([])  # 没有查询参数
        print(f"Output from test_execute_no_query: {result}")
        self.assertEqual(result, "Error: No search query provided.")  # 确认返回错误消息

    def test_execute_request_exception(self):
        """
        测试在请求异常时的处理。
        """
        original_base_url = self.search_tool.base_url  # 保存原始URL
        self.search_tool.base_url = "http://invalid_url"  # 临时设置无效URL
        try:
            result = self.search_tool.execute([self.valid_query])  # 执行查询
            print(f"Output from test_execute_request_exception: {result}")
            self.assertTrue("Error during search" in result)  # 确保返回错误信息
        finally:
            self.search_tool.base_url = original_base_url  # 恢复原始基础URL

    def test_execute_no_results(self):
        """
        测试查询没有结果时的处理。
        """
        result = self.search_tool.execute(["nonexistent query that should return no results"])  # 执行没有结果的查询
        print(f"Output from test_execute_no_results: {result}")
        self.assertTrue(isinstance(result, str), "Result should be a string.")  # 确保返回的是字符串
        if result == "":
            print("Warning: SearxNG returned no results for a query that should have returned no results.")  # 警告信息，结果为空

    def test_execution_failure_check_error(self):
        """
        测试执行失败时的错误检查。
        """
        output = "Error: Something went wrong"
        self.assertTrue(self.search_tool.execution_failure_check(output))  # 确保识别出错误

    def test_execution_failure_check_no_error(self):
        """
        测试执行成功时的错误检查。
        """
        output = "Search completed successfully"
        self.assertFalse(self.search_tool.execution_failure_check(output))  # 确保没有错误

if __name__ == '__main__':
    unittest.main()  # 运行单元测试
