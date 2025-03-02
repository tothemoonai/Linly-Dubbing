import json
import os
import time
import traceback
from loguru import logger
from .step000_video_downloader import get_info_list_from_url, download_single_video, get_target_folder
from .step010_demucs_vr import separate_all_audio_under_folder, init_demucs, release_model
from .step020_asr import transcribe_all_audio_under_folder
from .step021_asr_whisperx import init_whisperx, init_diarize
from .step022_asr_funasr import init_funasr
from .step030_translation import translate_all_transcript_under_folder
from .step040_tts import generate_all_wavs_under_folder
from .step042_tts_xtts import init_TTS
from .step043_tts_cosyvoice import init_cosyvoice
from .step050_synthesize_video import synthesize_all_video_under_folder
from concurrent.futures import ThreadPoolExecutor, as_completed

# 跟踪模型初始化状态
models_initialized = {
    'demucs': False,
    'xtts': False,
    'cosyvoice': False,
    'whisperx': False,
    'diarize': False,
    'funasr': False
}


def initialize_models(tts_method, asr_method, diarization):
    """
    初始化所需的模型。
    只在第一次调用时初始化模型，避免重复加载。
    """
    # 使用全局状态跟踪已初始化的模型
    global models_initialized

    with ThreadPoolExecutor() as executor:
        try:
            # Demucs模型初始化
            if not models_initialized['demucs']:
                executor.submit(init_demucs)
                models_initialized['demucs'] = True
                logger.info("Demucs模型初始化完成")
            else:
                logger.info("Demucs模型已初始化，跳过")

            # TTS模型初始化
            if tts_method == 'xtts' and not models_initialized['xtts']:
                executor.submit(init_TTS)
                models_initialized['xtts'] = True
                logger.info("XTTS模型初始化完成")
            elif tts_method == 'cosyvoice' and not models_initialized['cosyvoice']:
                executor.submit(init_cosyvoice)
                models_initialized['cosyvoice'] = True
                logger.info("CosyVoice模型初始化完成")

            # ASR模型初始化
            if asr_method == 'WhisperX':
                if not models_initialized['whisperx']:
                    executor.submit(init_whisperx)
                    models_initialized['whisperx'] = True
                    logger.info("WhisperX模型初始化完成")
                if diarization and not models_initialized['diarize']:
                    executor.submit(init_diarize)
                    models_initialized['diarize'] = True
                    logger.info("Diarize模型初始化完成")
            elif asr_method == 'FunASR' and not models_initialized['funasr']:
                executor.submit(init_funasr)
                models_initialized['funasr'] = True
                logger.info("FunASR模型初始化完成")

        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(f"初始化模型失败: {str(e)}\n{stack_trace}")
            # 出现错误时，重置初始化状态
            models_initialized = {key: False for key in models_initialized}
            release_model()  # 释放已加载的模型
            raise


def process_video(info, root_folder, resolution,
                  demucs_model, device, shifts,
                  asr_method, whisper_model, batch_size, diarization, whisper_min_speakers, whisper_max_speakers,
                  translation_method, translation_target_language,
                  tts_method, tts_target_language, voice,
                  subtitles, speed_up, fps, background_music, bgm_volume, video_volume,
                  target_resolution, max_retries):
    local_time = time.localtime()

    for retry in range(max_retries):
        try:
            if isinstance(info, str) and info.endswith('.mp4'):
                folder = os.path.dirname(info)
                # os.rename(info, os.path.join(folder, 'download.mp4'))
            else:
                folder = get_target_folder(info, root_folder)
                if folder is None:
                    error_msg = f'无法获取视频目标文件夹: {info["title"]}'
                    logger.warning(error_msg)
                    return False, None, error_msg

                folder = download_single_video(info, root_folder, resolution)
                if folder is None:
                    error_msg = f'下载视频失败: {info["title"]}'
                    logger.warning(error_msg)
                    return False, None, error_msg

            logger.info(f'处理视频: {folder}')

            try:
                status, vocals_path, _ = separate_all_audio_under_folder(
                    folder, model_name=demucs_model, device=device, progress=True, shifts=shifts)
                logger.info(f'人声分离完成: {vocals_path}')
            except Exception as e:
                stack_trace = traceback.format_exc()
                error_msg = f'人声分离失败: {str(e)}\n{stack_trace}'
                logger.error(error_msg)
                return False, None, error_msg

            try:
                status, result_json = transcribe_all_audio_under_folder(
                    folder, asr_method=asr_method, whisper_model_name=whisper_model, device=device,
                    batch_size=batch_size, diarization=diarization,
                    min_speakers=whisper_min_speakers,
                    max_speakers=whisper_max_speakers)
                logger.info(f'语音识别完成: {status}')
            except Exception as e:
                stack_trace = traceback.format_exc()
                error_msg = f'语音识别失败: {str(e)}\n{stack_trace}'
                logger.error(error_msg)
                return False, None, error_msg

            try:
                status, summary, translation = translate_all_transcript_under_folder(
                    folder, method=translation_method, target_language=translation_target_language)
                logger.info(f'翻译完成: {status}')
            except Exception as e:
                stack_trace = traceback.format_exc()
                error_msg = f'翻译失败: {str(e)}\n{stack_trace}'
                logger.error(error_msg)
                return False, None, error_msg

            try:
                status, synth_path, _ = generate_all_wavs_under_folder(
                    folder, method=tts_method, target_language=tts_target_language, voice=voice)
                logger.info(f'语音合成完成: {synth_path}')
            except Exception as e:
                stack_trace = traceback.format_exc()
                error_msg = f'语音合成失败: {str(e)}\n{stack_trace}'
                logger.error(error_msg)
                return False, None, error_msg

            try:
                status, output_video = synthesize_all_video_under_folder(
                    folder, subtitles=subtitles, speed_up=speed_up, fps=fps, resolution=target_resolution,
                    background_music=background_music, bgm_volume=bgm_volume, video_volume=video_volume)
                logger.info(f'视频合成完成: {output_video}')
            except Exception as e:
                stack_trace = traceback.format_exc()
                error_msg = f'视频合成失败: {str(e)}\n{stack_trace}'
                logger.error(error_msg)
                return False, None, error_msg

            return True, output_video, "处理成功"
        except Exception as e:
            stack_trace = traceback.format_exc()
            error_msg = f'处理视频时发生错误 {info["title"] if isinstance(info, dict) else info}: {str(e)}\n{stack_trace}'
            logger.error(error_msg)
            if retry < max_retries - 1:
                logger.info(f'尝试重试 {retry + 2}/{max_retries}...')
            else:
                return False, None, error_msg

    return False, None, f"达到最大重试次数: {max_retries}"


def do_everything(root_folder, url, num_videos=5, resolution='1080p',
                  demucs_model='htdemucs_ft', device='auto', shifts=5,
                  asr_method='WhisperX', whisper_model='large', batch_size=32, diarization=False,
                  whisper_min_speakers=None, whisper_max_speakers=None,
                  translation_method='LLM', translation_target_language='简体中文',
                  tts_method='xtts', tts_target_language='中文', voice='zh-CN-XiaoxiaoNeural',
                  subtitles=True, speed_up=1.00, fps=30,
                  background_music=None, bgm_volume=0.5, video_volume=1.0, target_resolution='1080p',
                  max_workers=3, max_retries=5):
    try:
        success_list = []
        fail_list = []
        error_details = []

        # 记录处理开始信息和所有参数
        logger.info("-" * 50)
        logger.info(f"开始处理任务: {url}")
        logger.info(f"参数: 输出文件夹={root_folder}, 视频数量={num_videos}, 分辨率={resolution}")
        logger.info(f"人声分离: 模型={demucs_model}, 设备={device}, 移位次数={shifts}")
        logger.info(f"语音识别: 方法={asr_method}, 模型={whisper_model}, 批大小={batch_size}")
        logger.info(f"翻译: 方法={translation_method}, 目标语言={translation_target_language}")
        logger.info(f"语音合成: 方法={tts_method}, 目标语言={tts_target_language}, 声音={voice}")
        logger.info(f"视频合成: 字幕={subtitles}, 速度={speed_up}, FPS={fps}, 分辨率={target_resolution}")
        logger.info("-" * 50)

        url = url.replace(' ', '').replace('，', '\n').replace(',', '\n')
        urls = [_ for _ in url.split('\n') if _]

        # 初始化模型（改用新的初始化函数）
        try:
            initialize_models(tts_method, asr_method, diarization)
        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(f"初始化模型失败: {str(e)}\n{stack_trace}")
            return f"初始化模型失败: {str(e)}", None

        out_video = None
        if url.endswith('.mp4'):
            try:
                import shutil
                # 获取原始视频文件名（不带路径）
                original_file_name = os.path.basename(url)

                # 去除文件扩展名，生成文件夹名称
                new_folder_name = os.path.splitext(original_file_name)[0]

                # 构建新文件夹的完整路径
                new_folder_path = os.path.join(root_folder, new_folder_name)

                # 在 root_folder 下创建该文件夹
                os.makedirs(new_folder_path, exist_ok=True)

                # 构建原始文件的完整路径
                original_file_path = os.path.join(root_folder, original_file_name)

                # 构建新位置的完整路径
                new_file_path = os.path.join(new_folder_path, "download.mp4")

                # 将视频文件移动到新创建的文件夹中并重命名
                shutil.copy(original_file_path, new_file_path)
                # 在 root_folder 下创建该文件夹
                os.makedirs(new_folder_path, exist_ok=True)

                success, output_video, error_msg = process_video(
                    new_file_path, root_folder, resolution,
                    demucs_model, device, shifts,
                    asr_method, whisper_model, batch_size, diarization, whisper_min_speakers, whisper_max_speakers,
                    translation_method, translation_target_language,
                    tts_method, tts_target_language, voice,
                    subtitles, speed_up, fps, background_music, bgm_volume, video_volume,
                    target_resolution, max_retries
                )

                if success:
                    logger.info(f"视频处理成功: {new_file_path}")
                    return '处理成功', output_video
                else:
                    logger.error(f"视频处理失败: {new_file_path}, 错误: {error_msg}")
                    return f'处理失败: {error_msg}', None
            except Exception as e:
                stack_trace = traceback.format_exc()
                logger.error(f"处理本地视频失败: {str(e)}\n{stack_trace}")
                return f"处理本地视频失败: {str(e)}", None
        else:
            try:
                videos_info = []
                for video_info in get_info_list_from_url(urls, num_videos):
                    videos_info.append(video_info)

                if not videos_info:
                    return "获取视频信息失败，请检查URL是否正确", None

                for info in videos_info:
                    try:
                        success, output_video, error_msg = process_video(
                            info, root_folder, resolution,
                            demucs_model, device, shifts,
                            asr_method, whisper_model, batch_size, diarization, whisper_min_speakers,
                            whisper_max_speakers,
                            translation_method, translation_target_language,
                            tts_method, tts_target_language, voice,
                            subtitles, speed_up, fps, background_music, bgm_volume, video_volume,
                            target_resolution, max_retries
                        )

                        if success:
                            success_list.append(info)
                            out_video = output_video
                            logger.info(f"成功处理视频: {info['title'] if isinstance(info, dict) else info}")
                        else:
                            fail_list.append(info)
                            error_details.append(f"{info['title'] if isinstance(info, dict) else info}: {error_msg}")
                            logger.error(
                                f"处理视频失败: {info['title'] if isinstance(info, dict) else info}, 错误: {error_msg}")
                    except Exception as e:
                        stack_trace = traceback.format_exc()
                        fail_list.append(info)
                        error_details.append(f"{info['title'] if isinstance(info, dict) else info}: {str(e)}")
                        logger.error(
                            f"处理视频出错: {info['title'] if isinstance(info, dict) else info}, 错误: {str(e)}\n{stack_trace}")
            except Exception as e:
                stack_trace = traceback.format_exc()
                logger.error(f"获取视频列表失败: {str(e)}\n{stack_trace}")
                return f"获取视频列表失败: {str(e)}", None

        # 记录处理结果汇总
        logger.info("-" * 50)
        logger.info(f"处理完成: 成功={len(success_list)}, 失败={len(fail_list)}")
        if error_details:
            logger.info("失败详情:")
            for detail in error_details:
                logger.info(f"  - {detail}")

        return f'成功: {len(success_list)}\n失败: {len(fail_list)}', out_video

    except Exception as e:
        # 捕获整体处理过程中的任何错误
        stack_trace = traceback.format_exc()
        error_msg = f"处理过程中发生错误: {str(e)}\n{stack_trace}"
        logger.error(error_msg)
        return error_msg, None


if __name__ == '__main__':
    do_everything(
        root_folder='videos',
        url='https://www.bilibili.com/video/BV1kr421M7vz/',
        translation_method='LLM',
        # translation_method = 'Google Translate', translation_target_language = '简体中文',
    )