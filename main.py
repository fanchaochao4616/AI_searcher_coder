#!/usr/bin python3

import sys
import signal
import argparse
import configparser

# 从 sources 包导入 Provider、Interaction 类和 Agent 相关类
from sources.llm_provider import Provider
from sources.interaction import Interaction
from sources.agents import Agent, CoderAgent, CasualAgent, FileAgent, PlannerAgent, BrowserAgent

import warnings
# 忽略警告信息
warnings.filterwarnings("ignore")

# 读取配置文件 config.ini
config = configparser.ConfigParser()
config.read('config.ini')


# 处理中断信号（Ctrl+C）的函数，退出程序
def handleInterrupt(signum, frame):
    sys.exit(0)


def main():
    # 注册 SIGINT 信号处理函数
    signal.signal(signal.SIGINT, handler=handleInterrupt)

    # 根据配置判断是否使用本地模型，创建 Provider 实例
    if config.getboolean('MAIN', 'is_local'):
        provider = Provider(config["MAIN"]["provider_name"], config["MAIN"]["provider_model"],
                            config["MAIN"]["provider_server_address"])
    else:
        provider = Provider(provider_name=config["MAIN"]["provider_name"],
                            model=config["MAIN"]["provider_model"],
                            server_address=config["MAIN"]["provider_server_address"])

    # 创建多个不同类型的 Agent 实例
    agents = [
        CasualAgent(model=config["MAIN"]["provider_model"],
                    name=config["MAIN"]["agent_name"],
                    prompt_path="prompts/casual_agent.txt",
                    provider=provider),
        CoderAgent(model=config["MAIN"]["provider_model"],
                   name="coder",
                   prompt_path="prompts/coder_agent.txt",
                   provider=provider),
        FileAgent(model=config["MAIN"]["provider_model"],
                  name="File Agent",
                  prompt_path="prompts/file_agent.txt",
                  provider=provider),
        PlannerAgent(model=config["MAIN"]["provider_model"],
                     name="Planner",
                     prompt_path="prompts/planner_agent.txt",
                     provider=provider),
        BrowserAgent(model=config["MAIN"]["provider_model"],
                     name="Browser",
                     prompt_path="prompts/browser_agent.txt",
                     provider=provider)
    ]

    # 创建 Interaction 实例，管理与用户的交互流程
    interaction = Interaction(agents, tts_enabled=config.getboolean('MAIN', 'speak'),
                              stt_enabled=config.getboolean('MAIN', 'listen'),
                              recover_last_session=config.getboolean('MAIN', 'recover_last_session'))

    try:
        # 主循环：持续获取用户输入并生成响应
        while interaction.is_active:
            interaction.get_user()  # 获取用户输入
            interaction.think()     # 模型思考并生成回答
            interaction.show_answer()  # 展示回答给用户
    except Exception as e:
        # 如果发生异常且配置允许保存会话，则保存当前会话状态
        if config.getboolean('MAIN', 'save_session'):
            interaction.save_session()
        raise e  # 抛出异常
    finally:
        # 不管是否发生异常，最后都尝试保存会话状态
        if config.getboolean('MAIN', 'save_session'):
            interaction.save_session()


# 程序入口点
if __name__ == "__main__":
    main()