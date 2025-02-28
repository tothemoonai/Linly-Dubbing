import os
import threading
import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QScrollArea, QPushButton, QMessageBox, QComboBox, QCheckBox,
                               QSplitter, QProgressBar, QTextEdit)
from PySide6.QtCore import QTimer, Signal, QObject, Qt

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


# 创建一个信号类用于线程通信
class WorkerSignals(QObject):
    finished = Signal(str, str)  # 完成信号：状态, 视频路径
    progress = Signal(int, str)  # 进度信号：百分比, 状态信息
    log = Signal(str)  # 日志信号：日志文本


class FullAutoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建主水平布局，左侧放配置项，右侧放处理按钮和视频播放器
        self.main_layout = QHBoxLayout(self)

        # 左侧配置区域
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)

        # 创建一个滚动区域用于容纳配置项
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        # 添加所有配置控件到左侧滚动区域

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
        self.translation_method.addItems(
            ['OpenAI', 'LLM', 'Google Translate', 'Bing Translate', 'Ernie', '火山引擎-deepseek', "deepseek-api",
             "阿里云-通义千问"])
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

        # 设置滚动区域
        self.scroll_area.setWidget(self.scroll_widget)
        self.left_layout.addWidget(self.scroll_area)

        # 右侧控制和显示区域
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)

        # 执行按钮区域
        self.button_layout = QHBoxLayout()

        # 执行按钮
        self.run_button = QPushButton("一键处理")
        self.run_button.clicked.connect(self.run_process)
        self.run_button.setMinimumHeight(50)

        # 停止按钮
        self.stop_button = QPushButton("停止处理")
        self.stop_button.clicked.connect(self.stop_process)
        self.stop_button.setMinimumHeight(50)
        self.stop_button.setEnabled(False)  # 初始禁用

        # 预览按钮
        self.preview_button = QPushButton("预览视频")
        self.preview_button.clicked.connect(self.preview_video)
        self.preview_button.setMinimumHeight(50)
        self.preview_button.setEnabled(False)  # 初始禁用

        # 添加按钮到按钮布局
        self.button_layout.addWidget(self.run_button)
        self.button_layout.addWidget(self.stop_button)
        self.button_layout.addWidget(self.preview_button)
        self.right_layout.addLayout(self.button_layout)

        # 进度条
        self.progress_layout = QVBoxLayout()
        self.progress_label = QLabel("准备就绪")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_layout.addWidget(QLabel("处理进度:"))
        self.progress_layout.addWidget(self.progress_bar)
        self.progress_layout.addWidget(self.progress_label)
        self.right_layout.addLayout(self.progress_layout)

        # 状态显示
        self.status_label = QLabel("准备就绪")
        self.right_layout.addWidget(QLabel("处理状态:"))
        self.right_layout.addWidget(self.status_label)

        # 创建右侧的垂直分割器，上方放视频播放器，下方放日志
        self.right_splitter = QSplitter(Qt.Vertical)

        # 视频播放器容器
        self.video_container = QWidget()
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.addWidget(QLabel("合成视频预览:"))
        self.video_player = VideoPlayer("合成视频")
        self.video_layout.addWidget(self.video_player)
        self.video_container.setLayout(self.video_layout)

        # 日志容器
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.addWidget(QLabel("处理日志:"))

        # 日志文本区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)  # 设置为只读
        self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)  # 自动换行
        self.log_layout.addWidget(self.log_text)

        # 日志控制按钮
        self.log_button_layout = QHBoxLayout()
        self.clear_log_button = QPushButton("清空日志")
        self.clear_log_button.clicked.connect(self.clear_log)
        self.save_log_button = QPushButton("保存日志")
        self.save_log_button.clicked.connect(self.save_log)
        self.log_button_layout.addWidget(self.clear_log_button)
        self.log_button_layout.addWidget(self.save_log_button)
        self.log_layout.addLayout(self.log_button_layout)

        self.log_container.setLayout(self.log_layout)

        # 添加视频和日志区域到右侧分割器
        self.right_splitter.addWidget(self.video_container)
        self.right_splitter.addWidget(self.log_container)

        # 设置初始分割比例 (60% 视频, 40% 日志)
        self.right_splitter.setSizes([600, 400])

        # 将分割器添加到右侧布局
        self.right_layout.addWidget(self.right_splitter)

        # 添加左右两个区域到主布局
        # 使用QSplitter允许用户调整左右两部分的宽度
        self.main_splitter = QSplitter()
        self.main_splitter.addWidget(self.left_widget)
        self.main_splitter.addWidget(self.right_widget)

        # 设置初始分割比例 (40% 左侧, 60% 右侧)
        self.main_splitter.setSizes([400, 600])

        self.main_layout.addWidget(self.main_splitter)
        self.setLayout(self.main_layout)

        # 处理线程
        self.worker_thread = None
        self.is_processing = False
        self.signals = WorkerSignals()
        self.signals.finished.connect(self.process_finished)
        self.signals.progress.connect(self.update_progress)
        self.signals.log.connect(self.append_log)

        # 存储生成的视频路径
        self.generated_video_path = None

        # 模拟进度更新计时器
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.simulate_progress)
        self.current_progress = 0
        self.progress_steps = [
            "下载视频...", "人声分离...", "AI智能语音识别...",
            "字幕翻译...", "AI语音合成...", "视频合成..."
        ]
        self.current_step = 0

        # 初始化日志
        self.append_log("系统初始化完成，准备就绪")

    def simulate_progress(self):
        """模拟进度更新，实际应用中应由实际处理进度替代"""
        if self.current_progress < 100:
            # 每个步骤大约16-17%的进度
            step_progress = self.current_progress % 17

            if step_progress == 0 and self.current_progress > 0:
                self.current_step = (self.current_step + 1) % len(self.progress_steps)
                self.append_log(f"开始{self.progress_steps[self.current_step]}")

            self.current_progress += 1
            self.progress_bar.setValue(self.current_progress)
            self.progress_label.setText(f"{self.progress_steps[self.current_step]} ({self.current_progress}%)")
        else:
            self.progress_timer.stop()

    def update_progress(self, progress, status):
        """更新处理进度"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(status)
        self.append_log(f"进度更新: {progress}% - {status}")

    def process_thread(self):
        """异步处理线程"""
        try:
            self.signals.log.emit("开始处理...")

            # 记录重要参数
            self.signals.log.emit(f"视频文件夹: {self.video_folder.text()}")
            self.signals.log.emit(f"视频URL: {self.video_url.text()}")
            self.signals.log.emit(f"分辨率: {self.resolution.value()}")

            # 更详细的参数记录
            self.signals.log.emit("-" * 50)
            self.signals.log.emit("处理参数:")
            self.signals.log.emit(f"下载视频数量: {self.video_count.value()}")
            self.signals.log.emit(f"分辨率: {self.resolution.value()}")
            self.signals.log.emit(f"人声分离模型: {self.model.value()}")
            self.signals.log.emit(f"计算设备: {self.device.value()}")
            self.signals.log.emit(f"移位次数: {self.shifts.value()}")
            self.signals.log.emit(f"ASR模型: {self.asr_model.currentText()}")
            self.signals.log.emit(f"WhisperX模型大小: {self.whisperx_size.value()}")
            self.signals.log.emit(f"翻译方法: {self.translation_method.currentText()}")
            self.signals.log.emit(f"TTS方法: {self.tts_method.currentText()}")
            self.signals.log.emit("-" * 50)

            # 实际的处理调用
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

            self.signals.log.emit(f"处理完成: {result}")
            if video_path:
                self.signals.log.emit(f"生成视频路径: {video_path}")

            # 处理完成，发送信号
            self.signals.finished.emit(result, video_path if video_path else "")

        except Exception as e:
            # 捕获并记录完整的堆栈跟踪信息
            import traceback
            stack_trace = traceback.format_exc()
            error_msg = f"处理失败: {str(e)}\n\n堆栈跟踪:\n{stack_trace}"
            self.signals.log.emit(error_msg)
            self.signals.finished.emit(f"处理失败: {str(e)}", "")

    def run_process(self):
        """开始处理"""
        if self.is_processing:
            return

        self.is_processing = True
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.preview_button.setEnabled(False)
        self.status_label.setText("正在处理...")

        # 重置进度
        self.current_progress = 0
        self.current_step = 0
        self.progress_bar.setValue(0)

        # 记录开始处理
        self.append_log("-" * 50)
        self.append_log(f"开始处理 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.append_log(f"视频URL: {self.video_url.text()}")

        # 创建并启动处理线程
        self.worker_thread = threading.Thread(target=self.process_thread)
        self.worker_thread.daemon = True
        self.worker_thread.start()

        # 启动模拟进度更新 (实际应用中由实际进度替代)
        self.progress_timer.start(100)  # 每100毫秒更新一次

    def stop_process(self):
        """停止处理"""
        if not self.is_processing:
            return

        # 在实际应用中，添加停止处理的逻辑
        self.progress_timer.stop()
        # TODO: 添加中断处理线程的代码

        self.is_processing = False
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("处理已停止")
        self.append_log("用户手动停止处理")

    def process_finished(self, result, video_path):
        """处理完成回调"""
        self.progress_timer.stop()
        self.progress_bar.setValue(100)
        self.progress_label.setText("处理完成!")

        self.is_processing = False
        self.run_button.setEnabled(True)  # 重新启用一键处理按钮
        self.stop_button.setEnabled(False)  # 禁用停止处理按钮
        self.status_label.setText(result)

        # 存储生成的视频路径
        self.generated_video_path = video_path

        # 记录处理完成
        self.append_log(f"处理完成 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.append_log(f"结果: {result}")

        # 如果有视频路径，启用预览按钮并加载视频
        if video_path and os.path.exists(video_path):
            self.preview_button.setEnabled(True)
            self.video_player.set_video(video_path)
            self.append_log(f"生成视频路径: {video_path}")
        else:
            self.append_log("未生成视频或视频路径无效")

    def preview_video(self):
        """预览生成的视频"""
        if self.generated_video_path and os.path.exists(self.generated_video_path):
            # 如果已经加载了视频，直接播放
            # 否则重新加载视频
            if not hasattr(self.video_player,
                           'video_path') or self.video_player.video_path != self.generated_video_path:
                self.video_player.set_video(self.generated_video_path)

            # 播放视频
            self.video_player.play_pause()
            self.append_log(f"预览视频: {self.generated_video_path}")

    def append_log(self, message):
        """添加日志信息"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        self.log_text.append(log_message)
        # 滚动到最底部
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.append_log("日志已清空")

    def save_log(self):
        """保存日志"""
        try:
            # 创建日志文件夹
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # 创建日志文件名
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(log_dir, f"process_log_{timestamp}.txt")

            # 保存日志内容
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())

            self.append_log(f"日志已保存到: {log_file}")
        except Exception as e:
            self.append_log(f"保存日志失败: {str(e)}")