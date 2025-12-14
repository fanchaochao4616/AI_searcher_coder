from kokoro import KPipeline
from IPython.display import display, Audio
import soundfile as sf
import subprocess
import re
import platform

audio_queue = queue.Queue()
done = False


class Speech():
    """
    Speech 是一个用于将文本转换为语音的类。
    """

    def __init__(self, language: str = "english") -> None:
        # 语言映射字典，用于指定语言的代码
        self.lang_map = {
            "english": 'a',
            "chinese": 'z',
            "french": 'f'
        }
        # 语音映射字典，指定每种语言对应的语音选项
        self.voice_map = {
            "english": ['af_alloy', 'af_bella', 'af_kore', 'af_nicole', 'af_nova', 'af_sky', 'am_echo', 'am_michael',
                        'am_puck'],
            "chinese": ['zf_xiaobei', 'zf_xiaoni', 'zf_xiaoxiao', 'zf_xiaoyi', 'zm_yunjian', 'zm_yunxi', 'zm_yunxia',
                        'zm_yunyang'],
            "french": ['ff_siwis']
        }
        self.pipeline = KPipeline(lang_code=self.lang_map[language])  # 使用指定语言初始化KPipeline
        self.voice = self.voice_map[language][2]  # 设置默认的语音
        self.speed = 1.2  # 设置语音的速度

    def speak(self, sentence: str, voice_number: int = 1):
        """
        使用AI模型将文本转换为语音并播放。

        参数:
            sentence (str): 要转换为语音的文本，文本将被预处理。
            voice_number (int, optional): 使用的语音索引，从语音映射中选择，默认值为1。
        """
        sentence = self.clean_sentence(sentence)  # 清理输入的文本
        self.voice = self.voice_map["english"][voice_number]  # 设置语音
        generator = self.pipeline(
            sentence, voice=self.voice,
            speed=self.speed, split_pattern=r'\n+'  # 按行分割文本
        )
        for i, (gs, ps, audio) in enumerate(generator):
            audio_file = 'sample.wav'
            display(Audio(data=audio, rate=24000, autoplay=i == 0), display_id=False)
            sf.write(audio_file, audio, 24000)  # 保存每个音频文件
            # 根据操作系统播放音频
            if platform.system().lower() == "windows":
                import winsound
                winsound.PlaySound(audio_file, winsound.SND_FILENAME)
            elif platform.system().lower() == "linux":
                subprocess.call(["aplay", audio_file])
            else:
                subprocess.call(["afplay", audio_file])

    def replace_url(self, url: re.Match) -> str:
        """
        用域名替换URL，若为IP地址则返回空字符串。
        参数:
            url (re.Match): 匹配对象，包含URL模式的匹配
        返回:
            str: 从URL中提取的域名，如果是IP地址，则返回空字符串
        """
        domain = url.group(1)
        if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain):  # 检查是否为IP地址
            return ''
        return domain

    def extract_filename(self, m: re.Match) -> str:
        """
        从路径中提取文件名。
        参数:
            m (re.Match): 匹配对象，包含路径模式的匹配
        返回:
            str: 从路径中提取的文件名
        """
        path = m.group()
        parts = re.split(r'/|\\', path)
        return parts[-1] if parts else path

    def shorten_paragraph(self, sentence):
        # TODO 找到更好的方式，避免TTS说的内容过长，尽量只说有用的信息
        """
        查找长段落（例如**说明**: <长文本>），并仅保留第一句话。
        参数:
            sentence (str): 要缩短的句子
        返回:
            str: 缩短后的句子
        """
        lines = sentence.split('\n')
        lines_edited = []
        for line in lines:
            if line.startswith('**'):
                lines_edited.append(line.split('.')[0])  # 只保留第一句话
            else:
                lines_edited.append(line)
        return '\n'.join(lines_edited)

    def clean_sentence(self, sentence):
        """
        清理并规范化文本，以便进行语音合成，去除技术元素。
        参数:
            sentence (str): 输入的文本
        返回:
            str: 清理后的文本，将URL替换为域名，去除代码块等
        """
        lines = sentence.split('\n')
        filtered_lines = [line for line in lines if re.match(r'^\s*[a-zA-Z]', line)]  # 过滤非字母开头的行
        sentence = ' '.join(filtered_lines)
        sentence = re.sub(r'`.*?`', '', sentence)  # 去除代码块
        sentence = re.sub(r'https?://(?:www\.)?([^\s/]+)(?:/[^\s]*)?', self.replace_url, sentence)  # 替换URL
        sentence = re.sub(r'\b[\w./\\-]+\b', self.extract_filename, sentence)  # 提取文件名
        sentence = re.sub(r'\b-\w+\b', '', sentence)  # 去除以“-”开头的单词
        sentence = re.sub(r'[^a-zA-Z0-9.,!? _ -]+', ' ', sentence)  # 只保留有效字符
        sentence = re.sub(r'\s+', ' ', sentence).strip()  # 去除多余的空格
        sentence = sentence.replace('.com', '')  # 替换“.com”为空字符串
        return sentence


if __name__ == "__main__":
    speech = Speech()  # 创建 Speech 实例
    tosay = """
    我查找了最近的新闻，使用的网站是 https://www.theguardian.com/world
    这里是如何列出文件的：
    ls -l -a -h
    服务器的IP地址是 192.168.1.1
    """
    for voice_idx in range(len(speech.voice_map["english"])):  # 遍历所有的英语语音
        print(f"语音 {voice_idx}")
        speech.speak(tosay, voice_idx)  # 使用指定的语音播放文本
