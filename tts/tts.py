import edge_tts
import pygame
import os
import time
import glob
import re

# 新增全局變數控制播放狀態
should_stop = False
pygame_initialized = False

def init_audio():
    global pygame_initialized
    if not pygame_initialized:
        pygame.mixer.init(frequency=44100)
        pygame_initialized = True

def cleanup_audio():
    global pygame_initialized
    if pygame_initialized:
        pygame.mixer.quit()
        pygame_initialized = False

def stop_playback():
    global should_stop
    should_stop = True
    if pygame_initialized:
        pygame.mixer.music.stop()

def text_to_speech_single(text, language='en'):
    try:
        voice = "en-US-AriaNeural" if language == 'en' else "zh-TW-HsiaoChenNeural"
        tmp_dir = os.path.join(os.path.dirname(__file__), 'tmp')
        os.makedirs(tmp_dir, exist_ok=True)
        output_file = os.path.join(tmp_dir, f"temp_{language}_{int(time.time())}.mp3")
        
        # 使用 asyncio.run 來同步執行異步操作
        communicate = edge_tts.Communicate(text, voice)
        try:
            import asyncio
            asyncio.run(communicate.save(output_file))
        except Exception as e:
            # print(f"Error saving audio: {e}")
            return None
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            return output_file
        else:
            print(f"Error: Generated file {output_file} is empty or does not exist")
            return None
    except Exception as e:
        print(f"Error processing {language} text: {e}")
        return None

def split_mixed_text(text):
    segments = []
    current_segment = ""
    current_type = None
    
    for char in text:
        is_chinese = '\u4e00' <= char <= '\u9fff'
        char_type = 'zh' if is_chinese else 'en'
        
        if current_type is None:
            current_type = char_type
        
        if char_type != current_type and current_segment:
            segments.append((current_segment.strip(), current_type))
            current_segment = ""
            current_type = char_type
            
        if char.strip():
            current_segment += char
    
    if current_segment:
        segments.append((current_segment.strip(), current_type))
    
    return segments

def split_into_phrases(text):
    """Split text into phrases based on punctuation and maintain language separation"""
    # First split by language
    mixed_segments = split_mixed_text(text)
    phrases = []
    
    for segment_text, lang in mixed_segments:
        # Split by punctuation while preserving it
        if lang == 'en':
            # For English, split by common punctuation
            sub_phrases = re.split(r'([.!?;]+\s*)', segment_text)
        else:
            # For Chinese, split by Chinese punctuation as well
            sub_phrases = re.split(r'([.!?;。！？；]+\s*)', segment_text)
        
        # Recombine punctuation with previous phrase
        current_phrase = ""
        for i in range(len(sub_phrases)):
            current_phrase += sub_phrases[i]
            if (i % 2 == 1 or i == len(sub_phrases) - 1) and current_phrase.strip():
                phrases.append((current_phrase.strip(), lang))
                current_phrase = ""
    
    return phrases

def text_to_speech(text):
    global should_stop, pygame_initialized
    should_stop = False
    try:
        # Split text into smaller phrases
        phrases = split_into_phrases(text)
        if not pygame_initialized:
            init_audio()
        
        for phrase_text, lang in phrases:
            if should_stop:
                break
            if phrase_text.strip():
                temp_file = text_to_speech_single(phrase_text, lang)
                if temp_file:
                    try:
                        pygame.mixer.music.load(temp_file)
                        pygame.mixer.music.play()
                        
                        start_time = time.time()
                        while pygame.mixer.music.get_busy() and not should_stop:
                            time.sleep(0.1)
                            if time.time() - start_time > 30:  # timeout protection
                                break
                    except pygame.error as e:
                        print(f"Error playing {temp_file}: {e}")
                    finally:
                        try:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                        except:
                            pass
        
        cleanup_audio()
        cleanup_temp_files()

    except Exception as e:
        print(f"Error in text_to_speech: {e}")
    finally:
        cleanup_temp_files()

def cleanup_temp_files():
    tmp_dir = os.path.join(os.path.dirname(__file__), 'tmp')
    for mp3_file in glob.glob(os.path.join(tmp_dir, "temp_*.mp3")):
        try:
            if os.path.exists(mp3_file):
                os.remove(mp3_file)
        except:
            pass

def test_tts(text: str):
    """
    測試文字轉語音功能的同步版本
    支援中英文混合文字

    Args:
        text (str): 要轉換的文字，可以是中英文混合
    
    Example:
        test_tts("Hello World! 你好世界！")
    """
    try:
        text_to_speech(text)
        return True
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return False

if __name__ == "__main__":
    # 測試案例
    test_texts = [
        "Hello! Testing English",
        "測試中文發音",
        "這是 Mixed 中英文測試 Test"
    ]
    
    print("Running TTS tests...")
    for text in test_texts:
        print(f"\nTesting: {text}")
        test_tts(text)