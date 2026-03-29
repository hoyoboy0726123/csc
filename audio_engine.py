import os
import database
from groq import Groq

def transcribe_audio(file_path):
    """
    使用 Groq Whisper API 進行轉譯。
    使用 verbose_json 並根據停頓時間自動斷句換行。
    """
    api_key = database.get_config("ACTIVE_KEY")
    if not api_key:
        return "尚未設定 Groq API Key。"
    
    try:
        client = Groq(api_key=api_key)
        
        # 繁體中文引導提示詞
        tc_prompt = "這是一段繁體中文的逐字稿，請確保輸出為繁體字並包含正確的標點符號。"

        with open(file_path, "rb") as file:
            response = client.audio.transcriptions.create(
                file=(os.path.basename(file_path), file.read()),
                model="whisper-large-v3",
                prompt=tc_prompt,
                response_format="verbose_json",
                language="zh",
                temperature=0.0
            )
        
        # 處理斷句換行
        return process_segments(response.segments)
        
    except Exception as e:
        return f"Groq 語音轉譯失敗: {str(e)}"

def process_segments(segments, pause_threshold=0.8):
    """
    根據時間戳記偵測語音停頓，自動插入換行符。
    支援字典 (dict) 或物件 (object) 格式。
    """
    full_text = ""
    
    def get_val(obj, key):
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    for i in range(len(segments)):
        current_s = segments[i]
        text = get_val(current_s, 'text').strip()
        
        full_text += text
        
        # 檢查與下一段的間隔
        if i < len(segments) - 1:
            next_s = segments[i+1]
            
            curr_end = get_val(current_s, 'end')
            next_start = get_val(next_s, 'start')
            
            if curr_end is not None and next_start is not None:
                pause_duration = next_start - curr_end
                
                # 若停頓超過閾值，或者當前片段以句末標點結尾，則換行
                if pause_duration > pause_threshold:
                    full_text += "\n"
                elif any(text.endswith(p) for p in ["。", "！", "？", "；"]):
                    full_text += "\n"
                else:
                    full_text += " "
            else:
                full_text += " "
                
    return full_text.strip()
