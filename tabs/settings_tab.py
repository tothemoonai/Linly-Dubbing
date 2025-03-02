import os
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
                               QPushButton, QMessageBox, QSplitter)
from PySide6.QtCore import Qt, Signal

from ui_components import (CustomSlider, FloatSlider, RadioButtonGroup,
                           AudioSelector, VideoPlayer)


class SettingsTab(QWidget):
    """
    配置页面，允许用户设置所有处理参数并保存到config.json
    """
    # 定义配置变更信号
    config_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_config()

    def init_ui(self):
        """初始化配置页面UI"""
        self.layout = QVBoxLayout(self)

        # 创建一个滚动区域用于容纳配置项
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        # 添加所有配置控件
        self.add_config_widgets()

        # 创建保存配置按钮
        self.button_layout = QHBoxLayout()
        self.save_config_button = QPushButton("保存配置")
        self.save_config_button.clicked.connect(self.save_config)
        self.save_config_button.setMinimumHeight(40)
        self.save_config_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.reset_config_button = QPushButton("重置配置")
        self.reset_config_button.clicked.connect(self.reset_config)
        self.reset_config_button.setMinimumHeight(40)
        self.button_layout.addWidget(self.reset_config_button)
        self.button_layout.addWidget(self.save_config_button)

        # 设置滚动区域
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def add_config_widgets(self):
        """添加所有配置控件"""
        # 视频配置
        self.scroll_layout.addWidget(QLabel("=== 视频下载配置 ==="))
        self.scroll_layout.addWidget(QLabel("视频输出文件夹"))
        self.video_folder = self.add_label_value("videos", "视频输出到此文件夹")

        # 分辨率
        self.resolution = RadioButtonGroup(
            ['4320p', '2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p'],
            "分辨率",
            '1080p'
        )
        self.scroll_layout.addWidget(self.resolution)

        # 下载视频数量
        self.video_count = CustomSlider(1, 100, 1, "下载视频数量", 5)
        self.scroll_layout.addWidget(self.video_count)

        # 音频处理配置
        self.scroll_layout.addWidget(QLabel("=== 音频处理配置 ==="))
        # 模型
        self.model = RadioButtonGroup(
            ['htdemucs', 'htdemucs_ft', 'htdemucs_6s', 'hdemucs_mmi', 'mdx', 'mdx_extra', 'mdx_q', 'mdx_extra_q',
             'SIG'],
            "人声分离模型",
            'htdemucs_ft'
        )
        self.scroll_layout.addWidget(self.model)

        # 计算设备
        self.device = RadioButtonGroup(['auto', 'cuda', 'cpu'], "计算设备", 'auto')
        self.scroll_layout.addWidget(self.device)

        # 移位次数
        self.shifts = CustomSlider(0, 10, 1, "移位次数 Number of shifts", 5)
        self.scroll_layout.addWidget(self.shifts)

        # ASR配置
        self.scroll_layout.addWidget(QLabel("=== 语音识别配置 ==="))
        # ASR模型选择
        self.asr_model_label = QLabel("ASR模型选择")
        self.scroll_layout.addWidget(self.asr_model_label)
        self.asr_model = RadioButtonGroup(['WhisperX', 'FunASR'], "ASR模型选择", 'WhisperX')
        self.scroll_layout.addWidget(self.asr_model)

        # WhisperX模型大小
        self.whisperx_size = RadioButtonGroup(['large', 'medium', 'small', 'base', 'tiny'], "WhisperX模型大小", 'large')
        self.scroll_layout.addWidget(self.whisperx_size)

        # 批处理大小
        self.batch_size = CustomSlider(1, 128, 1, "批处理大小 Batch Size", 32)
        self.scroll_layout.addWidget(self.batch_size)

        # 分离多个说话人
        self.separate_speakers = RadioButtonGroup([True, False], "分离多个说话人", True)
        self.scroll_layout.addWidget(self.separate_speakers)

        # 最小说话人数
        self.min_speakers = RadioButtonGroup([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], "最小说话人数", None)
        self.scroll_layout.addWidget(self.min_speakers)

        # 最大说话人数
        self.max_speakers = RadioButtonGroup([None, 1, 2, 3, 4, 5, 6, 7, 8, 9], "最大说话人数", None)
        self.scroll_layout.addWidget(self.max_speakers)

        # 翻译配置
        self.scroll_layout.addWidget(QLabel("=== 翻译配置 ==="))
        # 翻译方式
        self.translation_method_label = QLabel("翻译方式")
        self.scroll_layout.addWidget(self.translation_method_label)
        self.translation_method = RadioButtonGroup(
            ['OpenAI', 'LLM', 'Google Translate', 'Bing Translate', 'Ernie', '火山引擎-deepseek', "deepseek-api",
             "阿里云-通义千问","Ollama"], "翻译方式", 'LLM')
        self.scroll_layout.addWidget(self.translation_method)

        # 目标语言 (翻译)
        self.target_language_translation_label = QLabel("目标语言 (翻译)")
        self.scroll_layout.addWidget(self.target_language_translation_label)
        self.target_language_translation = RadioButtonGroup(
            ['简体中文', '繁体中文', 'English', 'Cantonese', 'Japanese', 'Korean'], "目标语言 (翻译)", '简体中文')
        self.scroll_layout.addWidget(self.target_language_translation)

        # TTS配置
        self.scroll_layout.addWidget(QLabel("=== 语音合成配置 ==="))
        # AI语音生成方法
        self.tts_method_label = QLabel("AI语音生成方法")
        self.scroll_layout.addWidget(self.tts_method_label)
        self.tts_method = RadioButtonGroup(['xtts', 'cosyvoice', 'EdgeTTS'], "AI语音生成方法", 'EdgeTTS')
        self.scroll_layout.addWidget(self.tts_method)

        # 目标语言 (TTS)
        self.target_language_tts_label = QLabel("目标语言 (TTS)")
        self.scroll_layout.addWidget(self.target_language_tts_label)
        self.target_language_tts = RadioButtonGroup(
            ['中文', 'English', '粤语', 'Japanese', 'Korean', 'Spanish', 'French'], "目标语言 (TTS)", '中文')
        self.scroll_layout.addWidget(self.target_language_tts)

        # EdgeTTS声音选择
        self.edge_tts_voice_label = QLabel("EdgeTTS声音选择")
        self.scroll_layout.addWidget(self.edge_tts_voice_label)
        self.edge_tts_voice = RadioButtonGroup(
            ['zh-CN-XiaoxiaoNeural', 'zh-CN-YunxiNeural', 'en-US-JennyNeural', 'ja-JP-NanamiNeural'],
            "EdgeTTS声音选择", 'zh-CN-XiaoxiaoNeural')
        self.scroll_layout.addWidget(self.edge_tts_voice)

        # 视频合成配置
        self.scroll_layout.addWidget(QLabel("=== 视频合成配置 ==="))
        # 添加字幕
        self.add_subtitles = RadioButtonGroup([True, False], "添加字幕", True)
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

        # 高级配置
        self.scroll_layout.addWidget(QLabel("=== 高级配置 ==="))
        # Max Workers
        self.max_workers = CustomSlider(1, 100, 1, "Max Workers", 1)
        self.scroll_layout.addWidget(self.max_workers)

        # Max Retries
        self.max_retries = CustomSlider(1, 10, 1, "Max Retries", 3)
        self.scroll_layout.addWidget(self.max_retries)

    def add_label_value(self, value, tooltip=None):
        """为简单的文本值创建一个标签"""
        label = QLabel(value)
        if tooltip:
            label.setToolTip(tooltip)
        self.scroll_layout.addWidget(label)
        return label

    def get_config(self):
        """从UI控件中获取当前配置"""
        config = {
            "video_folder": self.video_folder.text(),
            "resolution": self.resolution.value(),
            "video_count": self.video_count.value(),
            "model": self.model.value(),
            "device": self.device.value(),
            "shifts": self.shifts.value(),
            "asr_model": self.asr_model.value(),
            "whisperx_size": self.whisperx_size.value(),
            "batch_size": self.batch_size.value(),
            "separate_speakers": self.separate_speakers.value(),
            "min_speakers": self.min_speakers.value(),
            "max_speakers": self.max_speakers.value(),
            "translation_method": self.translation_method.value(),
            "target_language_translation": self.target_language_translation.value(),
            "tts_method": self.tts_method.value(),
            "target_language_tts": self.target_language_tts.value(),
            "edge_tts_voice": self.edge_tts_voice.value(),
            "add_subtitles": self.add_subtitles.value(),
            "speed_factor": self.speed_factor.value(),
            "frame_rate": self.frame_rate.value(),
            "background_music": self.background_music.value(),
            "bg_music_volume": self.bg_music_volume.value(),
            "video_volume": self.video_volume.value(),
            "output_resolution": self.output_resolution.value(),
            "max_workers": self.max_workers.value(),
            "max_retries": self.max_retries.value()
        }
        return config

    def apply_config(self, config):
        """将配置应用到UI控件"""
        # 应用各项设置
        try:
            self.video_folder.setText(config.get("video_folder", "videos"))
            self.resolution.buttons[self.resolution.buttons.index(
                next(b for o, b in self.resolution.buttons if o == config.get("resolution", "1080p")))][1].setChecked(
                True)
            self.video_count.setValue(config.get("video_count", 5))
            self.model.buttons[self.model.buttons.index(
                next(b for o, b in self.model.buttons if o == config.get("model", "htdemucs_ft")))][1].setChecked(True)
            self.device.buttons[self.device.buttons.index(
                next(b for o, b in self.device.buttons if o == config.get("device", "auto")))][1].setChecked(True)
            self.shifts.setValue(config.get("shifts", 5))
            self.asr_model.buttons[self.asr_model.buttons.index(
                next(b for o, b in self.asr_model.buttons if o == config.get("asr_model", "WhisperX")))][1].setChecked(
                True)
            self.whisperx_size.buttons[self.whisperx_size.buttons.index(
                next(b for o, b in self.whisperx_size.buttons if o == config.get("whisperx_size", "large")))][
                1].setChecked(True)
            self.batch_size.setValue(config.get("batch_size", 32))
            self.separate_speakers.buttons[self.separate_speakers.buttons.index(
                next(b for o, b in self.separate_speakers.buttons if o == config.get("separate_speakers", True)))][
                1].setChecked(True)
            self.min_speakers.buttons[self.min_speakers.buttons.index(
                next(b for o, b in self.min_speakers.buttons if o == config.get("min_speakers", None)))][1].setChecked(
                True)
            self.max_speakers.buttons[self.max_speakers.buttons.index(
                next(b for o, b in self.max_speakers.buttons if o == config.get("max_speakers", None)))][1].setChecked(
                True)
            self.translation_method.buttons[self.translation_method.buttons.index(
                next(b for o, b in self.translation_method.buttons if o == config.get("translation_method", "LLM")))][
                1].setChecked(True)
            self.target_language_translation.buttons[self.target_language_translation.buttons.index(next(
                b for o, b in self.target_language_translation.buttons if
                o == config.get("target_language_translation", "简体中文")))][1].setChecked(True)
            self.tts_method.buttons[self.tts_method.buttons.index(
                next(b for o, b in self.tts_method.buttons if o == config.get("tts_method", "EdgeTTS")))][1].setChecked(
                True)
            self.target_language_tts.buttons[self.target_language_tts.buttons.index(next(
                b for o, b in self.target_language_tts.buttons if o == config.get("target_language_tts", "中文")))][
                1].setChecked(True)
            self.edge_tts_voice.buttons[self.edge_tts_voice.buttons.index(next(
                b for o, b in self.edge_tts_voice.buttons if
                o == config.get("edge_tts_voice", "zh-CN-XiaoxiaoNeural")))][1].setChecked(True)
            self.add_subtitles.buttons[self.add_subtitles.buttons.index(
                next(b for o, b in self.add_subtitles.buttons if o == config.get("add_subtitles", True)))][
                1].setChecked(True)
            self.speed_factor.setValue(config.get("speed_factor", 1.00))
            self.frame_rate.setValue(config.get("frame_rate", 30))
            if config.get("background_music"):
                self.background_music.file_path.setText(config.get("background_music"))
            self.bg_music_volume.setValue(config.get("bg_music_volume", 0.5))
            self.video_volume.setValue(config.get("video_volume", 1.0))
            self.output_resolution.buttons[self.output_resolution.buttons.index(
                next(b for o, b in self.output_resolution.buttons if o == config.get("output_resolution", "1080p")))][
                1].setChecked(True)
            self.max_workers.setValue(config.get("max_workers", 1))
            self.max_retries.setValue(config.get("max_retries", 3))
        except Exception as e:
            QMessageBox.warning(self, "配置加载错误", f"加载配置时出错: {str(e)}")

    def save_config(self):
        """保存配置到JSON文件"""
        try:
            config = self.get_config()
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(config_dir, "config.json")

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            QMessageBox.information(self, "保存成功", f"配置已保存到 {config_path}")

            # 发送配置变更信号
            self.config_changed.emit(config)

        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存配置时出错: {str(e)}")

    def load_config(self):
        """从JSON文件加载配置"""
        try:
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(config_dir, "config.json")

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.apply_config(config)
        except Exception as e:
            QMessageBox.warning(self, "加载配置失败", f"加载配置时出错: {str(e)}")

    def reset_config(self):
        """重置配置为默认值"""
        if QMessageBox.question(self, "确认重置", "确定要重置所有配置到默认值吗？") == QMessageBox.Yes:
            # 应用默认配置
            default_config = {
                "video_folder": "videos",
                "resolution": "1080p",
                "video_count": 5,
                "model": "htdemucs_ft",
                "device": "auto",
                "shifts": 5,
                "asr_model": "WhisperX",
                "whisperx_size": "large",
                "batch_size": 32,
                "separate_speakers": True,
                "min_speakers": None,
                "max_speakers": None,
                "translation_method": "LLM",
                "target_language_translation": "简体中文",
                "tts_method": "EdgeTTS",
                "target_language_tts": "中文",
                "edge_tts_voice": "zh-CN-XiaoxiaoNeural",
                "add_subtitles": True,
                "speed_factor": 1.00,
                "frame_rate": 30,
                "background_music": None,
                "bg_music_volume": 0.5,
                "video_volume": 1.0,
                "output_resolution": "1080p",
                "max_workers": 1,
                "max_retries": 3
            }
            self.apply_config(default_config)
            QMessageBox.information(self, "重置成功", "所有配置已重置为默认值")