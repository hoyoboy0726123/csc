# Voice-to-Code Pipeline（V2C）

將語音構思轉化為可執行代碼的自動化流水線，15 分鐘內完成從想法到本地專案。

## 🚀 快速開始

### 前置需求
- Docker & Docker Compose
- 4 GB 以上可用記憶體
- 網路可存取 Google GenerativeAI 與 Groq API

### 一鍵啟動
```bash
git clone https://github.com/your-org/v2c.git
cd v2c
cp .env.example .env
# 編輯 .env 填入 GEMINI_API_KEY 與 GROQ_API_KEY
docker-compose up -d
```
瀏覽器開啟 http://localhost:3000 即可使用。

## 📁 專案結構
```
v2c/
├── backend/              # FastAPI 後端
│   ├── routers/          # 路由層（auth、upload、prd、code、fix）
│   ├── services/         # 商業邏輯（STT、LLM 編排、提示鏈、模型路由、ZIP 建構、加密）
│   ├── models/         # SQLAlchemy 模型
│   └── database/         # SQLite 連線與初始化
├── frontend/             # Next.js 前端
│   ├── pages/          # 頁面（登入、儀表板、PRD 編輯、程式碼預覽）
│   └── components/     # 共用元件（錄音、拖曳區、Monaco 編輯器、聊天面板、技術棧選擇器、ZIP 下載、錯誤回報、金鑰管理、配額橫幅）
├── whisper/            # 自建 Whisper-large-v3 容器
├── tests/              # 單元測試
└── docs/               # API 與部署文件
```

## 🔧 環境變數
| 變數 | 說明 | 預設值 |
|---|---|---|
| GEMINI_API_KEY | Google GenerativeAI 金鑰 | 必填 |
| GROQ_API_KEY | Groq API 金鑰 | 必填 |
| JWT_SECRET | JWT 簽署密鑰 | 隨機 32 字元 |
| WHISPER_MODEL | Whisper 模型名稱 | large-v3 |
| SQLITE_PATH | SQLite 檔案路徑 | ./data/v2c.db |
| ZIP_CACHE_DIR | ZIP 暫存目錄 | ./data/zips |

## 🧪 開發模式
```bash
# 後端
cd backend
pip install -r requirements.txt
python database/init_db.py
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

## 📦 生產部署
參考 [docs/DEPLOY.md](docs/DEPLOY.md) 取得 Nginx、HTTPS、Whisper GPU 加速等完整指引。

## 🧪 測試
```bash
# 後端
pytest tests/backend

# 前端
cd frontend
npm test
```

## 📌 核心流程
1. 登入後選擇「錄音 / 上傳音檔 / 文字」任一方式輸入需求
2. 後台呼叫 Whisper 轉文字，再透過 LLM Orchestrator 生成標準 PRD
3. 使用者可於對話面板進行 5 輪微調，確認後凍結 PRD
4. 系統依 PRD 關鍵字自動選擇技術棧（Python / React / Node.js）
5. 生成壓縮包，內含完整程式碼、依賴檔與 README，本地零配置啟動
6. 若運行報錯，貼上終端訊息即可觸發 AI 自動修復，重新打包下載

## 📊 指標儀表板
造訪 `/dashboard` 可查看：
- 專案成功生成率
- 平均端到端耗時
- 模型切換使用率
- 個人 7 日留存

## 🔐 安全規範
- 所有 API Key 皆以 AES-256 加密儲存，資料庫不落盤明文
- 前端僅將 Key 存於 LocalStorage，後端代理所有 LLM 請求
- 通過 Burp Suite 掃描無高風險漏洞

## 📚 API 文件
完整端點與範例請見 [docs/API.md](docs/API.md)

## 🤝 貢獻指南
歡迎提交 Issue 與 PR，請遵循 Conventional Commits 規範。

## 📄 授權
MIT License