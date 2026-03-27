# API 文件

## 1. 概覽
所有端點均以 `/api/v1` 為前綴，統一使用 JSON 格式交換資料。  
認證方式：JWT Bearer Token，登入後將 `access_token` 置於 Header `Authorization: Bearer <token>`。  
Base URL（本地開發）：`http://localhost:8000/api/v1`

---

## 2. 通用回應格式
成功回應直接回傳物件；錯誤統一如下：
```json
{
  "detail": "人類可讀錯誤訊息"
}
```
HTTP Status Code 對照  
- 200 / 201：成功  
- 400：參數錯誤  
- 401：未登入或 Token 失效  
- 403：權限不足  
- 404：資源不存在  
- 422：校驗失敗  
- 500：伺服器內部錯誤  

---

## 3. 端點清單

### 3.1 認證
#### POST /auth/register
註冊新帳號，密碼長度 ≥ 8。

**Request**
```json
{
  "email": "user@example.com",
  "password": "12345678"
}
```

**Response 201**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST /auth/login
登入，回傳 JWT。

**Request**
```json
{
  "email": "user@example.com",
  "password": "12345678"
}
```

**Response 200** 同註冊格式。

---

### 3.2 上傳與 STT
#### POST /upload/audio
上傳音檔（≤ 50 MB）並啟動語音轉文字任務。

**Headers**  
`Authorization: Bearer <token>`  
`Content-Type: multipart/form-data`

**Form 欄位**  
- `file`: binary，支援 mp3 / wav / m4a

**Response 201**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```

#### GET /upload/status/{task_id}
查詢轉寫進度。

**Response 200**
```json
{
  "status": "completed",
  "text": "我要一個代辦事項網站，使用 Next.js 與 SQLite"
}
```
`status` 列舉：processing / completed / failed

---

### 3.3 PRD 管理
#### POST /prd
依據語音文字或純文字生成 PRD。

**Request**
```json
{
  "input": "我要一個代辦事項網站，使用 Next.js 與 SQLite",
  "input_type": "text"
}
```
`input_type` 列舉：text / audio_task（需先完成 STT）

**Response 201**
```json
{
  "prd_id": "prd_7c8c77e0-6c6a-4b78-a8b1-3d5a5ce35a3a",
  "title": "Next.js 代辦事項網站",
  "prd_md": "# 專案名稱\n..."
}
```

#### GET /prd/{prd_id}
取得單份 PRD。

**Response 200**
```json
{
  "prd_id": "prd_7c8c77e0-6c6a-4b78-a8b1-3d5a5ce35a3a",
  "title": "Next.js 代辦事項網站",
  "prd_md": "# 專案名稱\n...",
  "editable": true,
  "created_at": "2024-06-20T12:34:56Z"
}
```

#### PATCH /prd/{prd_id}
以自然語言微調 PRD。

**Request**
```json
{
  "instruction": "把價格改為新台幣"
}
```

**Response 200**
```json
{
  "prd_md": "# 專案名稱\n..."
}
```

#### POST /prd/{prd_id}/freeze
凍結 PRD，後續才能生成代碼。

**Response 204** 無內容

---

### 3.4 代碼生成
#### POST /code/generate
依據已凍結 PRD 生成完整專案 ZIP。

**Request**
```json
{
  "prd_id": "prd_7c8c77e0-6c6a-4b78-a8b1-3d5a5ce35a3a",
  "stack": "nextjs",
  "model": "gemini"
}
```
`stack` 列舉：python / nextjs / nodejs  
`model` 列舉：gemini / groq（可留空，後端依配額自動選）

**Response 201**
```json
{
  "build_id": "build_3c90a7f0-9c22-4b78-a8b1-3d5a5ce35a3a",
  "status": "building"
}
```

#### GET /code/status/{build_id}
查詢建置進度。

**Response 200**
```json
{
  "status": "completed",
  "download_url": "/api/v1/code/download/build_3c90a7f0-9c22-4b78-a8b1-3d5a5ce35a3a"
}
```
`status` 列舉：building / completed / failed

#### GET /code/download/{build_id}
下載 ZIP。  
Headers 會帶 `Content-Disposition: attachment; filename="project.zip"`  
直接回傳 binary，無 JSON。

---

### 3.5 錯誤修復
#### POST /fix
上傳終端錯誤訊息，回傳 patch。

**Request**
```json
{
  "build_id": "build_3c90a7f0-9c22-4b78-a8b1-3d5a5ce35a3a",
  "error_log": "ModuleNotFoundError: No module named 'pandas'",
  "file_hint": "app.py"
}
```

**Response 200**
```json
{
  "patch": "diff --git a/app.py b/app.py\n...\n+import pandas as pd",
  "apply_command": "patch -p1 < fix.patch"
}
```

---

### 3.6 金鑰管理
#### GET /keys
取得已儲存的加密金鑰（僅回傳末 4 碼）。

**Response 200**
```json
{
  "gemini": "sk-...AbCd",
  "groq": "sk-...WnXy"
}
```

#### PUT /keys
更新金鑰，後端 AES-256 加密儲存。

**Request**
```json
{
  "gemini_key": "sk-...",
  "groq_key": "sk-..."
}
```
僅傳需要更新的欄位即可。

**Response 204**

---

### 3.7 配額
#### GET /quota
查詢今日剩餘額度。

**Response 200**
```json
{
  "usage": 73,
  "limit": 100,
  "reset_at": "2024-06-21T00:00:00Z"
}
```

---

## 4. WebSocket 事件
連線端點：`ws://localhost:8000/ws/{token}`  
伺服器推送格式：
```json
{
  "type": "prd_update",
  "data": {
    "prd_id": "prd_7c8c77e0-6c6a-4b78-a8b1-3d5a5ce35a3a",
    "delta": "新增功能..."
  }
}
```
`type` 列舉：prd_update / build_progress / build_done / error

---

## 5. 錯誤碼對照
| 錯誤碼 | 說明 |
|---|---|
| UPLOAD_001 | 音檔超過 50 MB |
| PRD_001 | PRD 尚未凍結無法生成代碼 |
| BUILD_001 | 模型限流，請稍後再試 |
| KEY_001 | 金鑰解密失敗，請重新上傳 |

---

## 6. 附錄
### 6.1 列舉值
- `input_type`: text, audio_task  
- `stack`: python, nextjs, nodejs  
- `model`: gemini, groq  
- `status` (STT): processing, completed, failed  
- `status` (Build): building, completed, failed  

### 6.2 Postman 集合
請匯入 `docs/V2C.postman_collection.json`（與本文件同步更新）

### 6.3 版本歷史
- v1.0 2024-06-20 初版，對應 MVP 功能