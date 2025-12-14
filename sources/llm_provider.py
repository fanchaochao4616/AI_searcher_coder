import time
import ollama
from ollama import chat
import requests
import subprocess
import ipaddress
import platform
from dotenv import load_dotenv, set_key
from openai import OpenAI
from huggingface_hub import InferenceClient
import os
import httpx


class Provider:
    def __init__(self, provider_name, model, server_address="127.0.0.1:5000"):
        self.provider_name = provider_name.lower()  # 提供者名称，统一转换为小写
        self.model = model  # 模型名称
        self.server = self.check_address_format(server_address)  # 检查服务器地址格式
        self.available_providers = {
            "ollama": self.ollama_fn,
            "server": self.server_fn,
            "openai": self.openai_fn,
            "huggingface": self.huggingface_fn
        }  # 可用的提供者字典
        self.api_key = None  # API密钥
        self.unsafe_providers = ["openai"]  # 不安全的提供者列表
        if self.provider_name not in self.available_providers:
            raise ValueError(f"未知的提供者: {provider_name}")
        if self.provider_name in self.unsafe_providers:
            print("警告：您正在使用API提供者，您的数据将被发送到云端。")
            self.get_api_key(self.provider_name)
        elif self.server != "":
            print(f"提供者 {provider_name} 已在 {self.server} 初始化")
        self.check_address_format(self.server)
        if not self.is_ip_online(self.server.split(':')[0]):
            raise Exception(f"服务器 {self.server} 离线。")

    def get_api_key(self, provider):
        load_dotenv()
        api_key_var = f"{provider.upper()}_API_KEY"  # 获取环境变量中的API密钥
        api_key = os.getenv(api_key_var)
        if not api_key:
            api_key = input(f"请输入您的 {provider} API 密钥：")
            set_key(".env", api_key_var, api_key)  # 将API密钥保存到环境变量
            load_dotenv()
        return api_key

    def check_address_format(self, address):
        """
        验证地址是否为有效的IP格式。
        """
        try:
            ip, port = address.rsplit(":", 1)
            if all(c.lower() in ".:abcdef0123456789" for c in ip):
                ipaddress.ip_address(ip)
            if not port.isdigit() or not (0 <= int(port) <= 65535):
                raise ValueError("端口号必须是0到65535之间的数字。")
        except ValueError as e:
            raise Exception(f"地址格式无效: {e}. 是否指定了端口号？")
        return address

    def respond(self, history, verbose=True):
        """
        使用选定的提供者生成文本。
        """
        llm = self.available_providers[self.provider_name]
        try:
            thought = llm(history, verbose)
        except ConnectionError as e:
            raise ConnectionError(f"{str(e)}\n连接到 {self.server} 失败。")
        except AttributeError as e:
            raise NotImplementedError(f"{str(e)}\n{self.provider_name} 是否已实现？")
        except Exception as e:
            raise Exception(f"提供者 {self.provider_name} 失败: {str(e)}") from e
        return thought

    def is_ip_online(self, ip_address):
        """
        通过发送ping请求检查IP地址是否在线。
        """
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', ip_address]
        try:
            output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            if output.returncode == 0:
                return True
            else:
                print("错误代码:", output)
                return False
        except subprocess.TimeoutExpired:
            print("超时")
            return True
        except Exception as e:
            print(f"is_ip_online 错误:\n{e}")
            return False

    def server_fn(self, history, verbose=False):
        """
        使用远程服务器与LLM生成文本。
        """
        thought = ""
        route_start = f"http://{self.server}/generate"

        if not self.is_ip_online(self.server.split(":")[0]):
            raise Exception(f"服务器 {self.server} 离线")

        try:
            requests.post(route_start, json={"messages": history})
            is_complete = False
            while not is_complete:
                response = requests.get(f"http://{self.server}/get_updated_sentence")
                thought = response.json()["sentence"]
                is_complete = bool(response.json()["is_complete"])
                time.sleep(2)
        except KeyError as e:
            raise f"{str(e)}\n\n发生了错误，您是否使用了正确的地址配置？"
        except Exception as e:
            raise e
        return thought

    def ollama_fn(self, history, verbose=False):
        """
        使用本地ollama服务器生成文本。
        """
        thought = ""
        try:
            stream = chat(
                model=self.model,
                messages=history,
                stream=True,
            )
            for chunk in stream:
                if verbose:
                    print(chunk['message']['content'], end='', flush=True)
                thought += chunk['message']['content']
        except httpx.ConnectError as e:
            raise Exception("\nOllama连接失败。如果服务器地址不是localhost，请不要将提供者设置为ollama") from e
        except ollama.ResponseError as e:
            if e.status_code == 404:
                print(f"正在下载 {self.model}...")
                ollama.pull(self.model)
            if "refused" in str(e).lower():
                raise Exception("Ollama连接失败。服务器是否已启动？") from e
            raise e
        return thought

    def huggingface_fn(self, history, verbose=False):
        """
        使用Huggingface生成文本。
        """
        client = InferenceClient(
            api_key=self.get_api_key("huggingface")
        )
        completion = client.chat.completions.create(
            model=self.model,
            messages=history,
            max_tokens=1024,
        )
        thought = completion.choices[0].message
        return thought.content

    def openai_fn(self, history, verbose=False):
        """
        使用OpenAI生成文本。
        """
        api_key = self.get_api_key("openai")
        client = OpenAI(api_key=api_key)
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=history
            )
            thought = response.choices[0].message.content
            if verbose:
                print(thought)
            return thought
        except Exception as e:
            raise Exception(f"OpenAI API 错误: {str(e)}") from e

    def test_fn(self, history, verbose=True):
        """
        这个函数用于进行测试。
        """
        thought = """
        这是来自测试提供者的响应。
        将提供者更改为 'ollama' 或 'server' 以获得真实响应。

        ```python
        print("Hello world from python")
        ```

        ```bash
        echo "Hello world from bash"
        ```
        """
        return thought


if __name__ == "__main__":
    provider = Provider("openai", "gpt-4o-mini")
    print(provider.respond(["user", "你好，你怎么样？"]))
