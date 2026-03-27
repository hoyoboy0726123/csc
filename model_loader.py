import os
import torch
from huggingface_hub import snapshot_download
from transformers import AutoModel, AutoTokenizer
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
            ignore_patterns=["*.msgpack", "*.h5", "*.ot"] # 節省空間，只下載必要的 pt/safetensors
        )
    else:
        print(f"Model already exists at {LOCAL_MODEL_DIR}")

@st.cache_resource
def load_model():
    """載入模型與分詞器，並快取資源。"""
    download_model()
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Mac MPS 支援
    if torch.backends.mps.is_available():
        device = "mps"
        
    print(f"Loading model on device: {device}")
    
    # 根據 SDD 提示，使用 trust_remote_code=True
    # 使用 float16 減少記憶體消耗 (CPU 則使用 float32)
    torch_dtype = torch.float16 if device != "cpu" else torch.float32
    
    try:
        model = AutoModel.from_pretrained(
            LOCAL_MODEL_DIR,
            trust_remote_code=True,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True
        ).to(device)
        
        tokenizer = AutoTokenizer.from_pretrained(
            LOCAL_MODEL_DIR,
            trust_remote_code=True
        )
        
        return model, tokenizer, device
    except Exception as e:
        print(f"Error loading model: {e}")
        st.error(f"模型載入失敗: {e}")
        return None, None, device

if __name__ == "__main__":
    # 測試下載與載入
    download_model()
    # load_model() # 不要在 cli 直接執行 load_model，因為它使用了 st.cache_resource
