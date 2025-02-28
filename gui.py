import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt

# 请确保导入正确模块
try:
    # 导入自定义控件文件
    from ui_components import (CustomSlider, FloatSlider, RadioButtonGroup,
                              AudioSelector, VideoPlayer)

    # 只导入全自动标签页
    from tabs.full_auto_tab import FullAutoTab

    # 尝试导入实际的功能模块
    try:
        from tools.step000_video_downloader import download_from_url
        from tools.step010_demucs_vr import separate_all_audio_under_folder
        from tools.step020_asr import transcribe_all_audio_under_folder
        from tools.step030_translation import translate_all_transcript_under_folder
        from tools.step040_tts import generate_all_wavs_under_folder
        from tools.step050_synthesize_video import synthesize_all_video_under_folder
        from tools.do_everything import do_everything
        from tools.utils import SUPPORT_VOICE
    except ImportError as e:
        print(f"警告: 无法导入一些工具模块: {e}")
        # 定义临时的支持语音列表
        SUPPORT_VOICE = ['zh-CN-XiaoxiaoNeural', 'zh-CN-YunxiNeural',
                        'en-US-JennyNeural', 'ja-JP-NanamiNeural']

except ImportError as e:
    print(f"错误: 初始化应用程序失败: {e}")
    sys.exit(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("智能视频多语言AI配音/翻译工具 - Linly-Dubbing")
        self.resize(1280, 768)  # 略微增加默认窗口大小，适应复杂UI

        # 直接使用全自动标签页作为中央窗口部件
        self.full_auto_tab = FullAutoTab()
        self.setCentralWidget(self.full_auto_tab)


def main():
    # 设置高DPI缩放
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle("Fusion")

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()