from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pyaudio import PyAudio
import sqlite3
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

app = FastAPI()

# 資料庫連結
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS prd
                 (id INTEGER PRIMARY KEY, content TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS code
                 (id INTEGER PRIMARY KEY, content TEXT)''')

# LLM 模型初始化
model = AutoModelForSeq2SeqLM.from_pretrained('t5-base')
tokenizer = AutoTokenizer.from_pretrained('t5-base')

@app.post('/generate_prd')
def generate_prd(audio_file: UploadFile = File(...)):
    # 音檔處理
    audio = PyAudio()
    stream = audio.open(format=audio.get_format_from_width(2),
                        channels=1,
                        rate=16000,
                        input=True,
                        frames_per_buffer=1024)
    frames = []
    while True:
        data = stream.read(1024)
        frames.append(data)
        if len(frames) > 100:
            break
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # 文字轉換
    text = tokenizer.decode(torch.randint(0, 100, (1, 100)).numpy(), skip_special_tokens=True)
    
    # PRD 生成
    input_ids = tokenizer.encode('Generate PRD: ' + text, return_tensors='pt')
    output = model.generate(input_ids)
    prd = tokenizer.decode(output[0], skip_special_tokens=True)
    
    # 儲存 PRD
    cursor.execute('INSERT INTO prd (content) VALUES (?)', (prd,))
    conn.commit()
    return JSONResponse(content={'prd': prd}, media_type='application/json')

@app.post('/generate_code')
def generate_code(prd_id: int):
    # 取得 PRD
    cursor.execute('SELECT content FROM prd WHERE id=?', (prd_id,))
    prd = cursor.fetchone()[0]
    
    # 代碼生成
    input_ids = tokenizer.encode('Generate code: ' + prd, return_tensors='pt')
    output = model.generate(input_ids)
    code = tokenizer.decode(output[0], skip_special_tokens=True)
    
    # 儲存代碼
    cursor.execute('INSERT INTO code (content) VALUES (?)', (code,))
    conn.commit()
    return JSONResponse(content={'code': code}, media_type='application/json')

@app.post('/fix_code')
def fix_code(code_id: int, error_message: str):
    # 取得代碼
    cursor.execute('SELECT content FROM code WHERE id=?', (code_id,))
    code = cursor.fetchone()[0]
    
    # 錯誤修復
    input_ids = tokenizer.encode('Fix code: ' + code + ' ' + error_message, return_tensors='pt')
    output = model.generate(input_ids)
    fixed_code = tokenizer.decode(output[0], skip_special_tokens=True)
    
    # 儲存修復後的代碼
    cursor.execute('UPDATE code SET content=? WHERE id=?', (fixed_code, code_id))
    conn.commit()
    return JSONResponse(content={'fixed_code': fixed_code}, media_type='application/json')
