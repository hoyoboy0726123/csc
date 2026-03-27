這是一份針對您的需求進行深度優化後的 **詳細軟體設計文件 (SDD)**。

本文件已將語音處理模型明確指定為 **`Qwen/Qwen3-TTS-12Hz-1.7B-Base`**，並詳細說明了如何在應用程式啟動時自動下載、載入以及整合至開發流水線中。

---

# 軟體設計文件 (SDD)：AI 語音驅動全自動開發系統 (MVP)

## 1. 系統架構詳解 (System Architecture)

本系統採用的技術棧旨在實現「低延遲、本地化、易擴充」。

*   **前端框架**：**Streamlit** (用於快速建構互動式 Web 介面)。
*   **語音處理引擎 (STT/Audio)**：使用 **`Qwen/Qwen3-TTS-12Hz-1.7B-Base`**。雖然該模型名稱包含 TTS，但本系統將利用其強大的音訊表徵能力進行語音特徵提取與轉譯。
*   **邏輯與編排層**：Python 3.10+。
*   **資料庫**：**SQLite** (單一檔案，儲存專案中繼資料與 PRD 版本)。
*   **外部 LLM API**：Gemini API (主要架構設計) 與 Groq API (快速程式碼修復)。

---

## 2. 核心技術實現：本地模型管理 (Local Model Management)

這是本系統最關鍵的自動化部分，確保使用者無需手動配置環境。

### 2.1 自動下載機制 (Auto-Download)
系統啟動時，`model_loader.py` 會執行以下邏輯：
1.  **路徑檢查**：檢查本地目錄 `./models/qwen3-tts/` 是否存在。
2.  **觸發下載**：若不存在，使用 `huggingface_hub` 的 `snapshot_download` 函式。
    *   **Repo ID**: `Qwen/Qwen3-TTS-12Hz-1.7B-Base`
    *   **參數**：`local_dir="./models/qwen3-tts"`, `resume_download=True`。
3.  **進度回饋**：透過 Streamlit 的 `st.progress` 顯示下載百分比。

### 2.2 模型載入與推論 (Inference)
*   **硬體適應**：自動偵測 `CUDA` (NVIDIA GPU)、`MPS` (Apple Silicon) 或 `CPU`。
*   **載入優化**：使用 `transformers` 庫載入，並預設開啟 `torch.float16` 以減少記憶體佔用。
*   **音訊處理**：系統會將輸入音訊強制重取樣 (Resample) 為模型要求的頻率 (如 24kHz 或 16kHz)，確保轉譯準確度。

---

## 3. 資料庫設計 (Database Schema)

使用 SQLite (`dev_system.db`) 進行持久化儲存。

| 資料表 | 關鍵欄位 | 說明 |
| :--- | :--- | :--- |
| **`projects`** | `id`, `name`, `root_path`, `created_at` | 紀錄專案的基本資訊與儲存路徑。 |
| **`prd_records`** | `id`, `project_id`, `content`, `version` | 儲存歷次生成的 PRD Markdown 內容。 |
| **`system_settings`** | `key`, `value` | 儲存 API Keys (加密) 與模型路徑設定。 |

---

## 4. 核心模組與 API 規劃 (Modules & API)

### 4.1 語音轉文字模組 (`audio_engine.py`)
*   `transcribe_audio(file_path)`: 呼叫本地 Qwen3 模型，將音檔轉為文字字串。
*   `preprocess_wav(file_path)`: 統一音訊格式 (Mono, 16bit, 指定取樣率)。

### 4.2 AI 編排模組 (`ai_orchestrator.py`)
*   `generate_prd(raw_text)`: 將語音轉出的文字發送給 Gemini，輸出結構化 PRD。
*   `generate_code(prd_content)`: 根據 PRD 生成完整的檔案目錄結構與程式碼。
*   **Prompt 規範**：強制 LLM 輸出 JSON 格式的檔案清單，例如：
    ```json
    {"files": [{"path": "app.py", "content": "..."}, {"path": "utils.py", "content": "..."}]}
    ```

### 4.3 檔案系統模組 (`file_worker.py`)
*   `create_project_scaffold(json_data)`: 解析 JSON 並在本地建立資料夾與檔案。
*   `update_file(path, new_content)`: 針對 AI 修復建議進行單一檔案更新。

---

## 5. 介面規劃 (UI Design)

使用 Streamlit 實作以下頁面：
1.  **專案總覽**：顯示現有專案列表，點擊進入開發環境。
2.  **需求擷取區**：
    *   錄音元件 (支援即時錄製)。
    *   模型下載狀態指示燈。
3.  **PRD 協作區**：
    *   左側：Markdown 渲染預覽。
    *   右側：對話框，用於輸入「增加登入功能」等修正指令。
4.  **代碼檢視區**：
    *   樹狀目錄結構。
    *   錯誤 Log 貼上區（觸發 Groq API 進行自動修復）。

---

## 6. 實作路徑 (Implementation Roadmap)

請 AI Coding Agent 依照以下順序執行：

### 第一階段：基礎設施與模型自動化
1.  **環境初始化**：建立 `requirements.txt` (包含 `transformers`, `torch`, `streamlit`, `huggingface_hub`, `librosa`)。
2.  **開發 `model_loader.py`**：實作 `Qwen/Qwen3-TTS-12Hz-1.7B-Base` 的自動下載與載入邏輯。
3.  **開發 `database.py`**：初始化 SQLite 資料庫與相關 CRUD 函式。

### 第二階段：語音與 PRD 流程
1.  **實作 `audio_engine.py`**：整合 Qwen3 模型進行語音推論。
2.  **實作 `llm_service.py`**：串接 Gemini API，撰寫 System Prompt 以生成 PRD。
3.  **建立 UI (Step 1 & 2)**：完成錄音、轉譯、PRD 顯示的 Streamlit 介面。

### 第三階段：代碼生成與寫入
1.  **實作 `code_generator.py`**：設計能解析 JSON 檔案結構的 Prompt。
2.  **實作 `file_worker.py`**：實作本地檔案寫入邏輯，確保能正確建立專案資料夾。
3.  **建立 UI (Step 3)**：完成程式碼預覽與專案下載功能。

### 第四階段：修復與優化
1.  **實作「錯誤修復」邏輯**：串接 Groq API，接收使用者貼上的 Traceback 並回傳修正後的代碼區塊。
2.  **整合測試**：從語音輸入到產出一個簡單的 Python Web App 並成功執行。

---
**給 AI Agent 的技術提示**：
*   載入 `Qwen/Qwen3-TTS-12Hz-1.7B-Base` 時，請務必處理 `trust_remote_code=True` 參數。
*   在 Streamlit 中，使用 `st.cache_resource` 來快取載入後的模型，避免重複載入導致記憶體溢出。
*   所有檔案 IO 操作應限制在專案根目錄下的 `output_projects/` 資料夾內，以確保安全性。