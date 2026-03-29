FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 拷貝 requirements.txt 到工作目錄
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 拷貝應用程式碼到工作目錄
COPY . .

# 暴露端口
EXPOSE 8501

# 運行命令
CMD ["streamlit", "run", "app.py"]