# 部署指南

本文件說明如何將 Voice-to-Code Pipeline（V2C）部署至本地開發、測試與正式環境。  
所有服務均以 Docker 映像封裝，支援 macOS / Linux / Windows（WSL2）。

---

## 1. 前置需求

| 工具 | 版本 | 備註 |
|---|---|---|
| Docker | ≥ 24.0 | 需支援 BuildKit |
| docker-compose | ≥ 2.20 | 建議使用 plugin 版本 |
| CPU 記憶體 | ≥ 8 GB | Whisper 容器獨佔 4 GB |
| 可用磁碟 | ≥ 20 GB | 含模型暫存與 ZIP 快取 |

---

## 2. 快速啟動（開發者體驗）

```bash
# 1. 複製專案
git clone https://github.com/your-org/v2c.git && cd v2c

# 2. 複製環境範本
cp .env.example .env
cp frontend/.env.example frontend/.env

# 3. 啟動全服務（含 Whisper、Backend、Frontend）
docker-compose up -d --build

# 4. 檢查健康狀態
curl http://localhost:8000/health
# 預期: {"status":"ok","ts":1719000000}

# 5. 開啟瀏覽器
open http://localhost:3000
```

首次啟動會自動建立 `data/v2c.db`（SQLite）與靜態目錄 `data/static`。  
如需停止：`docker-compose down -v`（-v 會一併清除 SQLite 與音檔快取）。

---

## 3. 環境變數說明

### 3.1 後端（.env）

```
# FastAPI
BACKEND_PORT=8000
SECRET_KEY=change-me-in-prod
CORS_ORIGINS=http://localhost:3000

# SQLite
SQLITE_PATH=./data/v2c.db

# 檔案上傳
UPLOAD_DIR=./data/static
MAX_AUDIO_SIZE_MB=50

# Whisper
WHISPER_URL=http://whisper:9000

# LLM 預設模型
DEFAULT_LLM=gemini
GEMINI_MODEL=gemini-1.5-pro
GROQ_MODEL=llama3-70b-8192

# 加密
MASTER_KEY=32-random-bytes-hex-string
```

### 3.2 前端（frontend/.env）

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### 3.3 Whisper 容器（docker-compose 已注入）

```
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cuda  # cpu 或 cuda
```

---

## 4. 正式環境部署

### 4.1 自建 Whisper（避免 OpenAI 限速）

```bash
# 1. 進入 whisper 目錄
cd whisper

# 2. 建置 GPU 映像（需 NVIDIA Container Toolkit）
docker build -f Dockerfile.whisper -t v2c/whisper:latest .

# 3. 執行
docker run -d --gpus all -p 9000:9000 --name whisper \
  -e WHISPER_MODEL=large-v3 \
  -v $(pwd)/data:/app/data \
  v2c/whisper:latest
```

### 4.2 使用外部 PostgreSQL（選配）

修改 `docker-compose.prod.yml`：

```yaml
services:
  backend:
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@db:5432/v2c
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: v2c
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

### 4.3 HTTPS 反向代理（Nginx）

```nginx
server {
    listen 443 ssl http2;
    server_name v2c.example.com;

    ssl_certificate     /etc/letsencrypt/live/v2c.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/v2c.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 5. 升級與版本控制

1. 拉取最新代碼  
   `git fetch origin && git checkout v1.x`

2. 重建映像  
   `docker-compose build --no-cache backend frontend`

3. 資料庫遷移（僅 PostgreSQL 需要）  
   `docker-compose exec backend alembic upgrade head`

4. 滾動重啟  
   `docker-compose up -d --force-recreate`

---

## 6. 監控與日誌

| 服務 | 路徑 | 說明 |
|---|---|---|
| FastAPI | `http://localhost:8000/metrics` | Prometheus 格式 |
| Nginx | `/var/log/nginx/access.log` | 反向代理日誌 |
| Whisper | `docker logs -f whisper` | 推理耗時與錯誤 |

建議在 `docker-compose.prod.yml` 加入 `logging` 區段，將日誌導向 Loki 或 AWS CloudWatch。

---

## 7. 常見問題

**Q1: 上傳音檔出現 413 Request Entity Too Large？**  
A: 在 `docker-compose.yml` 的 backend 服務加入：  
`NGINX_CLIENT_MAX_BODY_SIZE: 100m`

**Q2: Whisper 容器 GPU 無法載入？**  
A: 確認主機已安裝 NVIDIA Driver ≥ 525，並執行 `nvidia-smi` 能看到卡。

**Q3: 忘記 MASTER_KEY 導致無法解密金鑰？**  
A: 後端啟動時若偵測到已加密欄位但解密失敗，會立即退出並提示 `CryptoKeyError`。此時需重新生成金鑰並請用戶重新輸入 API Key。

---

## 8. 安全檢查清單

- [ ] `.env` 與 `data/` 已加入 `.gitignore`
- [ ] `MASTER_KEY` 長度 ≥ 32 bytes 且僅存於正式環境變數
- [ ] Whisper 容器僅監聽內網（docker network）或防火牆限制
- [ ] Nginx 開啟 HSTS 與 OCSP Stapling
- [ ] 定期執行 `docker scout cves` 檢查映像漏洞

---

## 9. 下一步

* 整合 Kubernetes Helm Chart（參考 `k8s/` 目錄，尚未開放）
* 加入 Prometheus Alertmanager 規則：PRD 生成失敗率 > 10 % 時告警
* 提供 Terraform 腳本一鍵部署至 AWS ECS

如需更多細節，請參閱 `docs/API.md` 或加入 Discord 支援頻道。