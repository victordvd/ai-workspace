from google import genai
from google.genai.types import GenerateContentConfig
from google.genai import types
import threading  # Move threading import to top with other imports
import time
import sys
import markdown
from bs4 import BeautifulSoup
import asyncio
from tts.tts import text_to_speech, stop_playback, init_audio, cleanup_audio
import os 

API_KEY='AIzaSyA_W6aECs79G2j4IdPrq16H3kqIFnXesio'

gemini_2_thinking_exp = 'gemini-2.0-flash-thinking-exp'
gemini_2_pro_exp = 'gemini-2.0-pro-exp-02-05'
gemini_2_flash = 'gemini-2.0-flash'
text_embedding_4 = 'text-embedding-004'

client = genai.Client(api_key=API_KEY, http_options={'api_version':'v1alpha'})  # Initialize the Gemini client

config = GenerateContentConfig(  # Configure the content generation
    temperature=1.2    # Set the desired temperature value here
)

instruction = """You are a English teacher for intermediate level student. If the user's question is in Chinese, translate it into English, and if it is in English, translate it into Chinese.
If the user's English words or grammar is wrong, correct it, 繁體中文 does not need to be corrected.
Answers should be based on 繁體中文 explanations, with as many extended examples as possible.
response should be mainly in English, with a small amount of 繁體中文, keep your responses under 500 words.
"""

async def print_char_by_char(text, delay=0.01):
    """
    逐字印出文字，帶有自然的打字效果
    """
    # 定義標點符號的停頓時間
    punctuation_delays = {
        ',': 0.3,
        '，': 0.3,
        '、': 0.3,
        '.': 0.4,
        '。': 0.4,
        '!': 0.4,
        '！': 0.4,
        '?': 0.4,
        '？': 0.4,
        ';': 0.3,
        '；': 0.3,
        ':': 0.3,
        '：': 0.3,
        '\n': 0.5,
    }

    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        pause_time = punctuation_delays.get(char, delay)
        await asyncio.sleep(pause_time)
    
    sys.stdout.write('\n')
    sys.stdout.flush()

def animate_loading():
    symbols = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    i = 0
    while loading_flag:
        sys.stdout.write('\r' + f"Processing {symbols[i]} ")
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(symbols)
    sys.stdout.write('\r' + ' ' * 20 + '\r')  # Clear the animation line and text
    sys.stdout.flush()

def markdown_to_text(md):
    # Convert Markdown to HTML
    html = markdown.markdown(md)
    # Convert HTML to plain text
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()

async def async_main():
    print("Welcome to English Teacher! (Type 'exit' or 'quit' to end the conversation)")
    global loading_flag, enable_tts, current_tts_thread
    
    # Ask user about text-to-speech at startup
    while True:
        choice = input("Would you like to enable text-to-speech? (yes/no): ").lower().strip()
        if choice in ['yes', 'y']:
            enable_tts = True
            break
        elif choice in ['no', 'n']:
            enable_tts = False
            break
        print("Please answer 'yes' or 'no'")
    
    if enable_tts:
        init_audio()  # Initialize audio system once at startup
    
    try:
        while True:
            quest = input("\nPlease enter your question: ").strip()
            
            if quest.lower() in ['exit', 'quit']:
                if current_tts_thread and current_tts_thread.is_alive():
                    stop_playback()
                    current_tts_thread.join(timeout=1)
                break
                
            if not quest:
                continue

            # Stop any current TTS playback
            if current_tts_thread and current_tts_thread.is_alive():
                stop_playback()
                current_tts_thread.join(timeout=1)

            loading_flag = True
            loading_thread = threading.Thread(target=animate_loading)
            loading_thread.start()

            contents = [
                {"role": "model", "parts": [{"text": instruction}]},
                {"role": "user", "parts": [{"text": quest}]}
            ]

            response = client.models.generate_content(
                model=gemini_2_pro_exp,#gemini_2_flash,
                contents=contents,
                config=config
            )

            loading_flag = False
            loading_thread.join()

            print("\nTeacher's response:")
            response_text = markdown_to_text(response.text)
            if enable_tts:
                current_tts_thread = threading.Thread(target=text_to_speech, args=(response_text,))
                current_tts_thread.daemon = True  # Allow the thread to be terminated on exit
                current_tts_thread.start()
            await print_char_by_char(response_text)

    finally:
        if enable_tts:
            cleanup_audio()  # Cleanup audio system on exit

def __main__():
    asyncio.run(async_main())

# Initialize the loading flag and tts flag
loading_flag = False
enable_tts = False
current_tts_thread = None

if __name__ == "__main__":
    __main__()