# AI 語音驅動全自動開發系統 (MVP)

這是一個從語音構思到可執行程式碼的自動化開發系統。透過口述需求，系統會自動生成 PRD，並根據 PRD 產出完整的專案原始碼。

## 🚀 核心功能
- **語音轉文字 (STT)**：使用 `Qwen3-TTS` 本地模型進行語音轉譯。
- **PRD 自動生成**：使用 `Gemini 2.0 Flash` 生成結構化產品需求文件。
- **全自動代碼生成**：根據 PRD 一鍵產出完整的專案目錄結構與代碼。
- **智慧錯誤修復**：整合 `Groq (Llama 3)`，貼上錯誤 Log 即可自動修正代碼。

## 🛠️ 環境準備

### 1. 安裝系統依賴 (Windows)
- 安裝 [SoX (Sound eXchange)](https://sourceforge.net/projects/sox/) 並將其加入系統環境變數 PATH。
- 建議使用 Python 3.12+。

### 2. 安裝 Python 套件
```cmd
pip install -r requirements.txt
```

### 3. 設定 API Keys
啟動系統後，在「系統設定」頁面配置以下 Key：
- **Gemini API Key**: 用於 PRD 與程式碼生成。
- **Groq API Key**: 用於快速錯誤修復。

## 🏃 啟動方式
```cmd
streamlit run app.py
```

## 📂 輸出說明
生成的專案將儲存在 `output_projects/` 資料夾中。

## ⚠️ 注意事項
- 第一次啟動時，系統會自動從 HuggingFace 下載 `Qwen3-TTS` 模型（約 4GB），請確保網路連線穩定。
- 建議配備 NVIDIA GPU 以獲得更快的推理速度。
