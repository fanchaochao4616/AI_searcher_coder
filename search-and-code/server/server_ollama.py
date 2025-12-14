from flask import Flask, jsonify, request
import threading
import ollama
import logging
import json

# 配置日志输出
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# 创建 Flask 应用
app = Flask(__name__)

# 共享状态和线程安全的锁
class Config:
    def __init__(self):
        self.model = None  # 当前模型
        self.known_models = []  # 已知的模型列表
        self.allowed_models = []  # 允许的模型列表
        self.model_name = None  # 模型名称

    def load(self):
        """加载配置文件"""
        with open('config.json', 'r') as f:
            data = json.load(f)
            self.known_models = data['known_models']
            self.model_name = data['model_name']

    def validate_model(self, model):
        """验证模型是否已知"""
        if model not in self.known_models:
            raise ValueError(f"模型 {model} 不在已知模型列表中")

# 生成状态类，管理生成过程中状态
class GenerationState:
    def __init__(self):
        self.lock = threading.Lock()  # 锁，确保线程安全
        self.last_complete_sentence = ""  # 上一个完整的句子
        self.current_buffer = ""  # 当前缓存的内容
        self.is_generating = False  # 是否正在生成
        self.model = None  # 当前使用的模型

state = GenerationState()  # 创建生成状态实例

def generate_response(history):  # 只接收历史消息作为参数
    global state
    try:
        with state.lock:  # 使用锁确保线程安全
            state.is_generating = True
            state.last_complete_sentence = ""
            state.current_buffer = ""

        # 调用 Ollama API 生成回复
        stream = ollama.chat(
            model=state.model,  # 直接访问当前模型
            messages=history,
            stream=True,  # 流式响应
        )
        # 逐步获取并处理返回的内容
        for chunk in stream:
            content = chunk['message']['content']
            print(content, end='', flush=True)
            with state.lock:
                state.current_buffer += content  # 将生成的内容追加到缓存

    except ollama.ResponseError as e:
        if e.status_code == 404:
            ollama.pull(state.model)  # 如果模型不存在，尝试下载
        with state.lock:
            state.is_generating = False
        print(f"错误: {e}")
    finally:
        with state.lock:
            state.is_generating = False  # 结束生成

# 定义一个路由，启动生成过程
@app.route('/generate', methods=['POST'])
def start_generation():
    global state
    data = request.get_json()  # 获取请求的 JSON 数据

    with state.lock:
        if state.is_generating:  # 如果已经在生成中，返回错误
            return jsonify({"error": "生成过程已在进行中"}), 400

        history = data.get('messages', [])  # 获取历史消息
        # 使用线程来进行生成，避免阻塞主线程
        threading.Thread(target=generate_response, args=(history,)).start()
    return jsonify({"message": "生成过程已启动"}), 202

# 定义一个路由，返回最新的生成内容
@app.route('/get_updated_sentence')
def get_updated_sentence():
    global state
    with state.lock:
        return jsonify({
            "sentence": state.current_buffer,  # 返回当前生成的内容
            "is_complete": not state.is_generating  # 如果正在生成，则返回 False
        })

# 程序入口
if __name__ == '__main__':
    config = Config()  # 创建配置实例
    config.load()  # 加载配置
    config.validate_model(config.model_name)  # 验证模型
    state.model = config.model_name  # 设置当前模型
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)  # 启动 Flask 应用
