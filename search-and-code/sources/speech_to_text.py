from colorama import Fore
import queue
import threading
import numpy as np
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import time
import librosa

audio_queue = queue.Queue()
done = False


class AudioRecorder:
    """
    AudioRecorder 类用于从麦克风录制音频并将其添加到音频队列中。
    """

    def __init__(self, format: int, channels: int = 1, rate: int = 4096, chunk: int = 8192, record_seconds: int = 5,
                 verbose: bool = False):
        import pyaudio
        self.format = format  # 音频格式
        self.channels = channels  # 声道数
        self.rate = rate  # 采样率
        self.chunk = chunk  # 每个数据块的大小
        self.record_seconds = record_seconds  # 录音时长
        self.verbose = verbose  # 是否启用详细模式
        self.audio = pyaudio.PyAudio()  # 初始化 PyAudio
        self.thread = threading.Thread(target=self._record, daemon=True)  # 启动一个线程来录音

    def _record(self) -> None:
        """
        从麦克风录制音频并将其添加到音频队列中。
        """
        stream = self.audio.open(format=self.format, channels=self.channels, rate=self.rate,
                                 input=True, frames_per_buffer=self.chunk)
        if self.verbose:
            print(Fore.GREEN + "AudioRecorder: 开始录音..." + Fore.RESET)

        while not done:
            frames = []
            for _ in range(0, int(self.rate / self.chunk * self.record_seconds)):
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    frames.append(data)
                except Exception as e:
                    print(Fore.RED + f"AudioRecorder: 读取流时失败 - {e}" + Fore.RESET)

            raw_data = b''.join(frames)
            audio_data = np.frombuffer(raw_data, dtype=np.int16)
            audio_queue.put((audio_data, self.rate))  # 将音频数据添加到队列
            if self.verbose:
                print(Fore.GREEN + "AudioRecorder: 将音频块添加到队列中" + Fore.RESET)

        stream.stop_stream()
        stream.close()
        self.audio.terminate()
        if self.verbose:
            print(Fore.GREEN + "AudioRecorder: 停止录音" + Fore.RESET)

    def start(self) -> None:
        """启动录音线程"""
        self.thread.start()

    def join(self) -> None:
        """等待录音线程完成"""
        self.thread.join()


class Transcript:
    """
    Transcript 类用于将音频队列中的音频转录并将其添加到转录内容中。
    """

    def __init__(self):
        self.last_read = None
        device = self.get_device()  # 获取设备（CPU 或 GPU）
        torch_dtype = torch.float16 if device == "cuda" else torch.float32  # 设置数据类型

        model_id = "distil-whisper/distil-medium.en"  # 使用的模型
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=torch_dtype, use_safetensors=True
        )
        model.to(device)  # 将模型移至指定设备
        processor = AutoProcessor.from_pretrained(model_id)

        self.pipe = pipeline(
            "automatic-speech-recognition",  # 使用自动语音识别管道
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=24,  # 人类在7秒内大约说20个token
            torch_dtype=torch_dtype,
            device=device,
        )

    def get_device(self) -> str:
        """获取可用设备，优先使用 MPS 或 CUDA"""
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda:0"
        else:
            return "cpu"

    def remove_hallucinations(self, text: str) -> str:
        """去除模型生成的幻觉文本"""
        common_hallucinations = ['Okay.', 'Thank you.', 'Thank you for watching.', 'You\'re', 'Oh', 'you', 'Oh.', 'Uh',
                                 'Oh,', 'Mh-hmm', 'Hmm.', 'going to.', 'not.']
        for hallucination in common_hallucinations:
            text = text.replace(hallucination, "")
        return text

    def transcript_job(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """转录音频数据"""
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max  # 转换为float32类型
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)  # 如果是多声道音频，转换为单声道
        if sample_rate != 16000:
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)  # 如果采样率不为16000，进行重采样
        result = self.pipe(audio_data)  # 使用管道进行转录
        return self.remove_hallucinations(result["text"])


class AudioTranscriber:
    """
    AudioTranscriber 类用于将音频从音频队列中转录并添加到转录内容中。
    """

    def __init__(self, ai_name: str, verbose: bool = False):
        self.verbose = verbose
        self.ai_name = ai_name  # 设置AI的名字，用于触发词
        self.transcriptor = Transcript()  # 初始化转录器
        self.thread = threading.Thread(target=self._transcribe, daemon=True)  # 启动转录线程
        self.trigger_words = {
            'EN': [f"{self.ai_name}"],
            'FR': [f"{self.ai_name}"],
            'ZH': [f"{self.ai_name}"],
            'ES': [f"{self.ai_name}"]
        }
        self.confirmation_words = {
            'EN': ["do it", "go ahead", "execute", "run", "start", "thanks", "would ya", "please", "okay?", "proceed",
                   "continue", "go on", "do that", "go it", "do you understand?"],
            'FR': ["fais-le", "vas-y", "exécute", "lance", "commence", "merci", "tu veux bien", "s'il te plaît",
                   "d'accord ?", "poursuis", "continue", "vas-y", "fais ça", "compris"],
            'ZH_CHT': ["做吧", "繼續", "執行", "運作看看", "開始", "謝謝", "可以嗎", "請", "好嗎", "進行", "做吧", "go",
                       "do it", "執行吧", "懂了"],
            'ZH_SC': ["做吧", "继续", "执行", "运作看看", "开始", "谢谢", "可以吗", "请", "好吗", "运行", "做吧", "go",
                      "do it", "执行吧", "懂了"],
            'ES': ["hazlo", "adelante", "ejecuta", "corre", "empieza", "gracias", "lo harías", "por favor", "¿vale?",
                   "procede", "continúa", "sigue", "haz eso", "haz esa cosa"]
        }
        self.recorded = ""  # 存储转录内容

    def get_transcript(self) -> str:
        """获取转录的内容"""
        global done
        buffer = self.recorded
        self.recorded = ""
        done = False
        return buffer

    def _transcribe(self) -> None:
        """
        使用AI的STT模型转录音频数据。
        """
        global done
        if self.verbose:
            print(Fore.BLUE + "AudioTranscriber: 开始处理..." + Fore.RESET)

        while not done or not audio_queue.empty():
            try:
                audio_data, sample_rate = audio_queue.get(timeout=1.0)  # 从队列中获取音频数据

                start_time = time.time()
                text = self.transcriptor.transcript_job(audio_data, sample_rate)  # 转录音频数据
                end_time = time.time()
                self.recorded += text  # 追加转录内容
                print(Fore.YELLOW + f"转录内容: {text} 用时 {end_time - start_time} 秒" + Fore.RESET)

                # 检测触发词
                for language, words in self.trigger_words.items():
                    if any(word in text.lower() for word in words):
                        print(Fore.GREEN + f"继续监听..." + Fore.RESET)
                        self.recorded = text
                # 检测确认词
                for language, words in self.confirmation_words.items():
                    if any(word in text.lower() for word in words):
                        print(Fore.GREEN + f"检测到触发词，发送到AI..." + Fore.RESET)
                        audio_queue.task_done()
                        done = True
                        break
            except queue.Empty:
                time.sleep(0.1)
                continue
            except Exception as e:
                print(Fore.RED + f"AudioTranscriber: 错误 - {e}" + Fore.RESET)
        if self.verbose:
            print(Fore.BLUE + "AudioTranscriber: 停止处理" + Fore.RESET)

    def start(self):
        """启动转录线程"""
        self.thread.start()

    def join(self):
        """等待转录线程完成"""
        self.thread.join()


if __name__ == "__main__":
    recorder = AudioRecorder(verbose=True)  # 创建录音对象
    transcriber = AudioTranscriber(verbose=True, ai_name="jarvis")  # 创建转录对象
    recorder.start()  # 启动录音
    transcriber.start()  # 启动转录
    recorder.join()  # 等待录音完成
    transcriber.join()  # 等待转录完成
