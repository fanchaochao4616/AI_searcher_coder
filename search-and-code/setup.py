from setuptools import setup, find_packages

# 读取项目的 README 文件，用于 long_description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 设置项目的包信息
setup(
    name="agenticSeek",  # 项目名称
    version="0.1.0",  # 项目版本
    author="Fosowl",  # 作者名称
    author_email="mlg.fcu@gmail.com",  # 作者邮箱
    description="A Python project for agentic search and processing",  # 项目简短描述
    long_description=long_description,  # 项目详细描述，通常从 README 文件读取
    long_description_content_type="text/markdown",  # long_description 的格式类型，这里使用 Markdown 格式
    url="https://github.com/Fosowl/agenticSeek",  # 项目主页地址
    packages=find_packages(),  # 查找并包含所有的包（目录）
    include_package_data=True,  # 包含项目中的所有非 Python 文件（如静态文件、模板等）

    # 安装项目时需要的依赖库
    install_requires=[
        "requests==2.31.0",  # HTTP 请求库
        "openai==1.61.1",  # OpenAI API 库
        "colorama==0.4.6",  # 命令行颜色输出
        "python-dotenv==1.0.0",  # 读取环境变量
        "playsound==1.3.0",  # 播放声音
        "soundfile==0.13.1",  # 处理声音文件
        "transformers==4.48.3",  # Huggingface 的 Transformers 库
        "torch==2.5.1",  # PyTorch
        "ollama==0.4.7",  # ollama 库，用于聊天生成
        "scipy==1.15.1",  # 科学计算库
        "kokoro==0.7.12",  # Kokoro 库
        "flask==3.1.0",  # Flask Web 框架
        "protobuf==3.20.3",  # Protobuf 库
        "termcolor==2.5.0",  # 终端颜色支持
        "gliclass==0.1.8",  # 用于图像分类的库
        "ipython==8.34.0",  # IPython，改进的 Python 交互式 shell
        "librosa==0.10.2.post1",  # 音频分析库
        "selenium==4.29.0",  # 自动化测试工具
        "markdownify==1.1.0",  # 将 Markdown 转换为 HTML
        "httpx>=0.27,<0.29",  # 高性能异步 HTTP 客户端
        "anyio>=3.5.0,<5",  # 异步 I/O 库
        "distro>=1.7.0,<2",  # 获取操作系统信息
        "jiter>=0.4.0,<1",  # Jiter 库
        "sniffio",  # 网络协议库
        "tqdm>4"  # 用于显示进度条
    ],

    # 可选的额外依赖项，用户可以选择安装
    extras_require={
        "chinese": [
            "ordered_set",  # 有序集合
            "pypinyin",  # 拼音库
            "cn2an",  # 中文数字转换库
            "jieba",  # 中文分词库
        ],
    },

    # 定义命令行脚本入口
    entry_points={
        "console_scripts": [
            "agenticseek=main:main",  # 创建一个命令行工具，执行 main.py 中的 main() 函数
        ],
    },

    # 项目分类
    classifiers=[
        "Programming Language :: Python :: 3",  # 适用于 Python 3
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",  # 项目的许可证类型
        "Operating System :: OS Independent",  # 跨平台
    ],

    # 指定 Python 版本要求
    python_requires=">=3.6",  # Python 最低版本要求为 3.6
)
