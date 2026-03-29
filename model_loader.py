import os
import torch
from huggingface_hub import snapshot_download
import streamlit as st

MODEL_REPO = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
LOCAL_MODEL_DIR = "./models/qwen3-tts"

def download_model():
    """下載模型到本地目錄。"""
    if not os.path.exists(LOCAL_MODEL_DIR):
        print(f"Downloading model {MODEL_REPO} to {LOCAL_MODEL_DIR}...")
        snapshot_download(
            repo_id=MODEL_REPO,
            local_dir=LOCAL_MODEL_DIR,
            resume_download=True,
            ignore_patterns=["*.msgpack", "*.h5", "*.ot"]
        )
    else:
        print(f"Model already exists at {LOCAL_MODEL_DIR}")

@st.cache_resource
def load_model():
    """載入模型與分詞器，並快取資源。"""
    download_model()
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if torch.backends.mps.is_available():
        device = "mps"
        
    print(f"Loading model on device: {device}")
    
    # Qwen3 模型建議使用 bfloat16 或 float16
    torch_dtype = torch.bfloat16 if device != "cpu" and torch.cuda.is_bf16_supported() else torch.float32
    
    try:
        # 強制使用 qwen_tts 套件載入，這是處理 qwen3_tts 架構的正確方式
        from qwen_tts import Qwen3TTSModel, Qwen3TTSTokenizer
        
        print("Detected qwen_tts package, loading specialized model class...")
        tokenizer = Qwen3TTSTokenizer.from_pretrained(LOCAL_MODEL_DIR)
        model = Qwen3TTSModel.from_pretrained(
            LOCAL_MODEL_DIR,
            torch_dtype=torch_dtype,
            device_map=device
        )
        
        return model, tokenizer, device
        
    except Exception as e:
        print(f"Specialized load failed: {e}")
        st.warning(f"專用載入失敗，嘗試使用 AutoModel (請確保 transformers >= 4.57.3): {e}")
        
        try:
            from transformers import AutoModel, AutoTokenizer
            # 注意：如果 local 沒有 .py 檔案，這裡必須確保 transformers 已經內建支援 qwen3_tts
            model = AutoModel.from_pretrained(
                LOCAL_MODEL_DIR,
                trust_remote_code=True,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True
            ).to(device)
            tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_DIR, trust_remote_code=True)
            return model, tokenizer, device
        except Exception as final_e:
            st.error(f"模型載入最終失敗。請執行 'uv add \"transformers>=4.57.3\"' 並重新啟動。 \n錯誤訊息: {final_e}")
            return None, None, device

if __name__ == "__main__":
    download_model()
