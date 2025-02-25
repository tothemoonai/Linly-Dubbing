import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QScrollArea, QPushButton, QMessageBox, QComboBox, QCheckBox)

from ui_components import (CustomSlider, FloatSlider, RadioButtonGroup,
                           AudioSelector, VideoPlayer)

# 尝试导入实际的功能模块
try:
    from tools.do_everything import do_everything
    from tools.utils import SUPPORT_VOICE
except ImportError:
    # 定义临时的支持语音列表
    SUPPORT_VOICE = ['zh-CN-XiaoxiaoNeural', 'zh-CN-YunxiNeural',
                     'en-US-JennyNeural', 'ja-JP-NanamiNeural']


class FullAutoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # 创建一个滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        # 视频输出文件夹
        self.video_folder = QLineEdit("videos")
        self.scroll_layout.addWidget(QLabel("视频输出文件夹"))
        self.scroll_layout.addWidget(self.video_folder)

        # 视频URL
        self.video_url = QLineEdit()
        self.video_url.setPlaceholderText("请输入Youtube或Bilibili的视频、播放列表或频道的URL")
        self.video_url.setText("https://www.bilibili.com/video/BV1kr421M7vz/")
        self.scroll_layout.addWidget(QLabel("视频URL"))
        self.scroll_layout.addWidget(self.video_url)

        # 下载视频数量
        self.video_count = CustomSlider(1, 100, 1, "下载视频数量", 5)
        self.scroll_layout.addWidget(self.video_count)

        # 分辨率
        self.resolution = RadioButtonGroup(
            ['4320p', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p'],
            "分辨率",
            '1080p'
        )
        self.scroll_layout.addWidget(self.resolution)

        # 模型
        self.model = RadioButtonGroup(
            ['htdemucs', 'htdemucs_ft', 'htdemucs_6s', 'hdemucs_mmi', 'mdx', 'mdx_extra', 'mdx_q', 'mdx_extra_q',
             'SIG'],
            "模型",
            'htdemucs_ft'
        )
        self.scroll_layout.addWidget(self.model)

        # 计算设备
        self.device = RadioButtonGroup(['auto', 'cuda', 'cpu'], "计算设备", 'auto')
        self.scroll_layout.addWidget(self.device)

        # 移位次数
        self.shifts = CustomSlider(0, 10, 1, "移位次数 Number of shifts", 5)
        self.scroll_layout.addWidget(self.shifts)

        # ASR模型选择
        self.asr_model = QComboBox()
        self.asr_model.addItems(['WhisperX', 'FunASR'])
        self.scroll_layout.addWidget(QLabel("ASR模型选择"))
        self.scroll_layout.addWidget(self.asr_model)

        # WhisperX模型大小
        self.whisperx_size = RadioButtonGroup(['large', 'medium', 'small', 'base', 'tiny'], "WhisperX模型大小", 'large')
        self.scroll_layout.addWidget(self.whisperx_size)

        # 批处理大小
        self.batch_size = CustomSlider(1, 128, 1, "批处理大小 Batch Size", 32)
        self.scroll_layout.addWidget(self.batch_size)

        # 分离多个说话人
        self.separate_speakers = QCheckBox("分离多个说话人")
        self.separate_speakers.setChecked(True)
        self.scroll_layout.addWidget(self.separate_speakers)

        # 最小说话人数
        self.min_speakers = RadioButtonGroup([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], "最小说话人数", None)
        self.scroll_layout.addWidget(self.min_speakers)

        # 最大说话人数
        self.max_speakers = RadioButtonGroup([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], "最大说话人数", None)
        self.scroll_layout.addWidget(self.max_speakers)

        # 翻译方式
        self.translation_method = QComboBox()
        self.translation_method.addItems(['OpenAI', 'LLM', 'Google Translate', 'Bing Translate', 'Ernie'])
        self.translation_method.setCurrentText('LLM')
        self.scroll_layout.addWidget(QLabel("翻译方式"))
        self.scroll_layout.addWidget(self.translation_method)

        # 目标语言 (翻译)
        self.target_language_translation = QComboBox()
        self.target_language_translation.addItems(
            ['简体中文', '繁体中文', 'English', 'Cantonese', 'Japanese', 'Korean'])
        self.scroll_layout.addWidget(QLabel("目标语言 (翻译)"))
        self.scroll_layout.addWidget(self.target_language_translation)

        # AI语音生成方法
        self.tts_method = QComboBox()
        self.tts_method.addItems(['xtts', 'cosyvoice', 'EdgeTTS'])
        self.scroll_layout.addWidget(QLabel("AI语音生成方法"))
        self.scroll_layout.addWidget(self.tts_method)

        # 目标语言 (TTS)
        self.target_language_tts = QComboBox()
        self.target_language_tts.addItems(['中文', 'English', '粤语', 'Japanese', 'Korean', 'Spanish', 'French'])
        self.target_language_tts.setCurrentText('中文')
        self.scroll_layout.addWidget(QLabel("目标语言 (TTS)"))
        self.scroll_layout.addWidget(self.target_language_tts)

        # EdgeTTS声音选择
        self.edge_tts_voice = QComboBox()
        self.edge_tts_voice.addItems(SUPPORT_VOICE)
        self.edge_tts_voice.setCurrentText('zh-CN-XiaoxiaoNeural')
        self.scroll_layout.addWidget(QLabel("EdgeTTS声音选择"))
        self.scroll_layout.addWidget(self.edge_tts_voice)

        # 添加字幕
        self.add_subtitles = QCheckBox("添加字幕")
        self.add_subtitles.setChecked(True)
        self.scroll_layout.addWidget(self.add_subtitles)

        # 加速倍数
        self.speed_factor = FloatSlider(0.5, 2, 0.05, "加速倍数", 1.00)
        self.scroll_layout.addWidget(self.speed_factor)

        # 帧率
        self.frame_rate = CustomSlider(1, 60, 1, "帧率", 30)
        self.scroll_layout.addWidget(self.frame_rate)

        # 背景音乐
        self.background_music = AudioSelector("背景音乐")
        self.scroll_layout.addWidget(self.background_music)

        # 背景音乐音量
        self.bg_music_volume = FloatSlider(0, 1, 0.05, "背景音乐音量", 0.5)
        self.scroll_layout.addWidget(self.bg_music_volume)

        # 视频音量
        self.video_volume = FloatSlider(0, 1, 0.05, "视频音量", 1.0)
        self.scroll_layout.addWidget(self.video_volume)

        # 分辨率 (输出)
        self.output_resolution = RadioButtonGroup(
            ['4320p', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p'],
            "输出分辨率",
            '1080p'
        )
        self.scroll_layout.addWidget(self.output_resolution)

        # Max Workers
        self.max_workers = CustomSlider(1, 100, 1, "Max Workers", 1)
        self.scroll_layout.addWidget(self.max_workers)

        # Max Retries
        self.max_retries = CustomSlider(1, 10, 1, "Max Retries", 3)
        self.scroll_layout.addWidget(self.max_retries)

        # 执行按钮
        self.run_button = QPushButton("一键处理")
        self.run_button.clicked.connect(self.run_process)
        self.scroll_layout.addWidget(self.run_button)

        # 状态显示
        self.status_label = QLabel("准备就绪")
        self.scroll_layout.addWidget(QLabel("处理状态:"))
        self.scroll_layout.addWidget(self.status_label)

        # 视频播放器
        self.video_player = VideoPlayer("合成视频样例结果")
        self.scroll_layout.addWidget(self.video_player)

        # 设置滚动区域
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)

    def run_process(self):
        # 这里应该调用原始的do_everything函数
        # 临时实现，实际应用中需要替换为真实的调用
        self.status_label.setText("处理中...")
        QMessageBox.information(self, "功能提示", "一键处理功能正在实现中...")

        # 实际应用中解除以下注释
        try:
            result, video_path = do_everything(
                self.video_folder.text(),
                self.video_url.text(),
                self.video_count.value(),
                self.resolution.value(),
                self.model.value(),
                self.device.value(),
                self.shifts.value(),
                self.asr_model.currentText(),
                self.whisperx_size.value(),
                self.batch_size.value(),
                self.separate_speakers.isChecked(),
                self.min_speakers.value(),
                self.max_speakers.value(),
                self.translation_method.currentText(),
                self.target_language_translation.currentText(),
                self.tts_method.currentText(),
                self.target_language_tts.currentText(),
                self.edge_tts_voice.currentText(),
                self.add_subtitles.isChecked(),
                self.speed_factor.value(),
                self.frame_rate.value(),
                self.background_music.value(),
                self.bg_music_volume.value(),
                self.video_volume.value(),
                self.output_resolution.value(),
                self.max_workers.value(),
                self.max_retries.value()
            )
            self.status_label.setText(result)
            if video_path and os.path.exists(video_path):
                self.video_player.set_video(video_path)
        except Exception as e:
            self.status_label.setText(f"处理失败: {str(e)}")