from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
from bs4 import BeautifulSoup
import markdownify
import logging
import sys


class Browser:
    def __init__(self, headless=False, anticaptcha_install=False):
        """初始化浏览器，支持无头模式和验证码解决方案"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
        }
        self.anticaptcha = "https://chrome.google.com/webstore/detail/nopecha-captcha-solver/dknlfmjaanfblgfdfebhijalfmhmjjjo/related"  # 防止验证码页面的链接
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")  # 开启无头模式
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            self.driver = webdriver.Chrome(options=chrome_options)  # 使用Chrome浏览器
            self.wait = WebDriverWait(self.driver, 10)  # 设置最大等待时间为10秒
            self.logger = logging.getLogger(__name__)
            self.logger.info("浏览器初始化成功")
        except Exception as e:
            raise Exception(f"浏览器初始化失败: {str(e)}")

    def go_to(self, url):
        """导航到指定的URL"""
        try:
            self.driver.get(url)
            time.sleep(2)  # 等待页面加载
            self.logger.info(f"成功导航到: {url}")
            return True
        except WebDriverException as e:
            self.logger.error(f"导航到 {url} 时发生错误: {str(e)}")
            return False

    def is_sentence(self, text):
        """检查文本是否符合有效的句子，或者是否包含重要的错误代码"""
        text = text.strip()
        error_codes = ["404", "403", "500", "502", "503"]  # 常见的错误码
        if any(code in text for code in error_codes):  # 如果包含错误代码，返回True
            return True
        words = text.split()
        word_count = len(words)
        has_punctuation = text.endswith(('.', '!', '?'))  # 检查是否有标点符号
        is_long_enough = word_count > 5  # 检查单词数是否大于5
        has_letters = any(word.isalpha() for word in words)  # 检查文本中是否有字母
        return (word_count >= 5 and (has_punctuation or is_long_enough) and has_letters)

    def get_text(self):
        """获取页面文本并转换为README（Markdown）格式"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # 去除页面中的不必要元素，如script和style
            for element in soup(['script', 'style']):
                element.decompose()

            text = soup.get_text()  # 获取页面的纯文本

            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk and self.is_sentence(chunk))

            # 将文本转换为Markdown格式
            markdown_text = markdownify.markdownify(text, heading_style="ATX")

            return markdown_text
        except Exception as e:
            self.logger.error(f"获取页面文本时发生错误: {str(e)}")
            return None

    def clean_url(self, url):
        """清理URL，移除无用的参数和哈希部分"""
        clean = url.split('#')[0]
        parts = clean.split('?', 1)
        base_url = parts[0]
        if len(parts) > 1:
            query = parts[1]
            essential_params = []
            for param in query.split('&'):
                if param.startswith('_skw=') or param.startswith('q=') or param.startswith('s='):
                    essential_params.append(param)
                elif param.startswith('_') or param.startswith('hash=') or param.startswith('itmmeta='):
                    break
            if essential_params:
                return f"{base_url}?{'&'.join(essential_params)}"
        return base_url

    def get_navigable(self):
        """获取当前页面上所有可导航的链接"""
        try:
            links = []
            elements = self.driver.find_elements(By.TAG_NAME, "a")  # 获取所有的<a>标签

            for element in elements:
                href = element.get_attribute("href")
                if href and href.startswith(("http", "https")):
                    links.append({
                        "url": href,
                        "text": element.text.strip(),
                        "is_displayed": element.is_displayed()  # 检查链接是否可见
                    })

            self.logger.info(f"发现 {len(links)} 个可导航链接")
            # 清理无效链接，返回前256字符以内的有效链接
            return [self.clean_url(link['url']) for link in links if link['is_displayed'] == True and len(link) < 256]
        except Exception as e:
            self.logger.error(f"获取可导航链接时发生错误: {str(e)}")
            return []

    def click_element(self, xpath):
        """点击指定XPath的元素"""
        try:
            element = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))  # 等待元素可点击
            )
            element.click()  # 点击元素
            time.sleep(2)  # 等待操作完成
            return True
        except TimeoutException:
            self.logger.error(f"元素未找到或不可点击: {xpath}")
            return False

    def get_current_url(self):
        """获取当前页面的URL"""
        return self.driver.current_url

    def get_page_title(self):
        """获取当前页面的标题"""
        return self.driver.title

    def scroll_bottom(self):
        """滚动到页面底部"""
        try:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"  # 执行JavaScript滚动到页面底部
            )
            time.sleep(1)  # 等待滚动完成
            return True
        except Exception as e:
            self.logger.error(f"滚动时发生错误: {str(e)}")
            return False

    def screenshot(self, filename):
        """截取当前页面的屏幕截图"""
        try:
            self.driver.save_screenshot(filename)  # 保存截图
            self.logger.info(f"截图已保存为 {filename}")
            return True
        except Exception as e:
            self.logger.error(f"截屏时发生错误: {str(e)}")
            return False

    def close(self):
        """关闭浏览器"""
        try:
            self.driver.quit()
            self.logger.info("浏览器已关闭")
        except Exception as e:
            raise e

    def __del__(self):
        """确保在销毁对象时关闭浏览器"""
        self.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)  # 设置日志级别为INFO

    browser = Browser(headless=False)  # 创建浏览器实例，设置为非无头模式

    try:
        browser.go_to("https://karpathy.github.io/")  # 访问目标网址
        text = browser.get_text()  # 获取页面的Markdown格式文本
        print("页面文本（Markdown格式）:")
        print(text)  # 打印页面内容
        links = browser.get_navigable()  # 获取页面中可导航的链接
        print("\n可导航链接:", links)  # 打印可导航链接
    finally:
        browser.close()  # 最后确保关闭浏览器
