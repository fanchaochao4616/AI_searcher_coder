from sources.text_to_speech import Speech
from sources.utility import pretty_print
from sources.router import AgentRouter
from sources.speech_to_text import AudioTranscriber, AudioRecorder


class Interaction:
    """
    Interaction 是一个处理用户与代理之间交互的类。
    它可以接收用户输入并将任务分配给代理，支持语音识别和语音合成功能。
    """

    def __init__(self, agents,
                 tts_enabled: bool = True,  # 是否启用语音合成功能
                 stt_enabled: bool = True,  # 是否启用语音识别功能
                 recover_last_session: bool = False):  # 是否恢复上次会话
        self.tts_enabled = tts_enabled  # 设置语音合成功能是否启用
        self.agents = agents  # 代理列表
        self.current_agent = None  # 当前使用的代理
        self.router = AgentRouter(self.agents)  # 代理路由，用于选择合适的代理处理任务
        self.speech = Speech()  # 语音合成对象
        self.is_active = True  # 活跃状态
        self.last_query = None  # 最后的用户输入
        self.last_answer = None  # 最后的代理回答
        self.ai_name = self.find_ai_name()  # 找到默认的AI名称，用于语音识别触发词
        self.tts_enabled = tts_enabled
        self.stt_enabled = stt_enabled
        if stt_enabled:
            self.transcriber = AudioTranscriber(self.ai_name, verbose=False)  # 语音转文字对象
            self.recorder = AudioRecorder()  # 音频录制对象
        if tts_enabled:
            self.speech.speak("Hello Sir, we are online and ready. What can I do for you ?")  # 开始时语音提示
        if recover_last_session:
            self.recover_last_session()  # 恢复上次会话

    def find_ai_name(self) -> str:
        """找到默认AI的名称。这个名称将作为语音识别的触发词。"""
        ai_name = "jarvis"  # 默认AI名称为jarvis
        for agent in self.agents:
            if agent.role == "talking":  # 如果代理角色是"talking"，即对话代理
                ai_name = agent.agent_name  # 获取该代理的名字
                break
        return ai_name

    def recover_last_session(self):
        """恢复上次会话的状态。"""
        for agent in self.agents:
            agent.memory.load_memory()  # 从每个代理的记忆中恢复上次会话

    def save_session(self):
        """保存当前会话的状态。"""
        for agent in self.agents:
            agent.memory.save_memory()  # 保存每个代理的记忆

    def is_active(self) -> bool:
        """返回代理是否处于活跃状态。"""
        return self.is_active

    def read_stdin(self) -> str:
        """从标准输入读取用户输入。"""
        buffer = ""

        PROMPT = "\033[1;35m➤➤➤ \033[0m"  # 提示符样式
        while buffer == "" or buffer.isascii() == False:  # 如果输入为空或不是ASCII字符，则继续提示用户输入
            try:
                buffer = input(PROMPT)  # 获取用户输入
            except EOFError:
                return None
            if buffer == "exit" or buffer == "goodbye":  # 用户输入exit或goodbye时，退出
                return None
        return buffer

    def transcription_job(self) -> str:
        """通过麦克风录制音频并进行语音转文字。"""
        self.recorder = AudioRecorder(verbose=True)  # 启动音频录制器
        self.transcriber = AudioTranscriber(self.ai_name, verbose=True)  # 启动语音转文字器
        self.transcriber.start()
        self.recorder.start()
        self.recorder.join()  # 等待录制结束
        self.transcriber.join()  # 等待转录完成
        query = self.transcriber.get_transcript()  # 获取转录结果
        return query

    def get_user(self) -> str:
        """获取用户输入，支持语音或键盘输入。"""
        if self.stt_enabled:  # 如果启用了语音转文字功能
            query = "TTS transcription of user: " + self.transcription_job()  # 通过语音转文字获取用户输入
        else:
            query = self.read_stdin()  # 否则通过键盘获取输入
        if query is None:
            self.is_active = False
            self.last_query = "Goodbye (exit requested by user, dont think, make answer very short)"
            return None
        self.last_query = query  # 保存用户输入
        return query

    def think(self) -> None:
        """请求AI代理处理用户输入并生成答案。"""
        if self.last_query is None or len(self.last_query) == 0:
            return
        agent = self.router.select_agent(self.last_query)  # 选择处理当前任务的代理
        if agent is None:
            return
        if self.current_agent != agent:
            self.current_agent = agent
            # 获取上一代理的历史记录
            self.current_agent.memory.push('user', self.last_query)
        self.last_answer, _ = agent.process(self.last_query, self.speech)  # 生成回答

    def show_answer(self) -> None:
        """展示答案给用户。"""
        if self.last_query is None:
            return
        self.current_agent.show_answer()  # 展示当前代理的回答
        if self.tts_enabled:
            self.speech.speak(self.last_answer)  # 如果启用了语音合成功能，则语音播报答案


if __name__ == "__main__":
    # 测试 Interaction 类的功能
    from llm_provider import Provider

    server_provider = Provider("server", "deepseek-r1:14b", "192.168.1.100:5000")

    # 创建 Interaction 实例
    agent = Interaction(agents=[], tts_enabled=True, stt_enabled=True)

    # 获取用户输入并处理
    ans = agent.get_user()
    agent.think()
    agent.show_answer()
    print(ans)  # 输出答案
