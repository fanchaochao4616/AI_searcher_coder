#!/bin/bash

echo "开始安装 Linux..."

# 更新包列表
sudo apt-get update

# 从 requirements.txt 安装 Python 依赖项
pip3 install -r requirements.txt

# 安装 Selenium for chromedriver
pip3 install selenium

# 为 pyAudio 安装 portaudio
sudo apt-get install -y portaudio19-dev python3-dev alsa-utils

echo "Linux 安装完成！"