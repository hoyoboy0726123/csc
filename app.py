import streamlit as st
import os
import time
import database
import audio_engine
import llm_service
import code_generator
import file_worker

# 頁面配置
st.set_page_config(page_title="AI 語音驅動全自動開發系統 (Groq 版)", layout="wide")

# 初始化資料庫
database.init_db()

def settings_page():
    st.title("⚙️ 全域系統設定")
    st.markdown("本系統已優化為完全使用 Groq LPU 加速，並支援本地 Qwen3 音訊處理。")

    # 讀取目前設定
    cur_key = database.get_config("ACTIVE_KEY", "")
    cur_model = database.get_config("ACTIVE_MODEL", "llama-3.3-70b-versatile")

    st.header("🤖 主模型設定 (LLM)")
    # 1. 金鑰輸入
    api_key = st.text_input("1. 輸入 Groq API Key", value=cur_key, type="password")
    
    # 2. 模型選擇 (動態獲取)
    model_options = []
    if api_key:
        with st.spinner("正在獲取 Groq 可用模型..."):
            model_options = llm_service.get_dynamic_models()
    
    if not model_options:
        model_options = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]

    selected_model = st.selectbox("2. 選擇主模型", options=model_options, 
                                  index=model_options.index(cur_model) if cur_model in model_options else 0)

    if st.button("🚀 測試並儲存 LLM 設定"):
        if not api_key:
            st.error("請輸入 API Key。")
        else:
            with st.spinner("正在測試 API 連線..."):
                success, msg = llm_service.test_connection(api_key, selected_model)
                if success:
                    database.save_config("ACTIVE_KEY", api_key)
                    database.save_config("ACTIVE_MODEL", selected_model)
                    database.save_config("ACTIVE_PROVIDER", "Groq")
                    st.success(f"已將 Groq / {selected_model} 設為主模型。")
                    st.rerun()
                else:
                    st.error(msg)

    st.divider()

    st.header("🔊 語音轉文字 (STT) 設定")
    cur_stt = database.get_config("AUDIO_ENGINE", "Groq-Whisper")
    stt_engine = st.radio("選擇語音處理方式", ["Groq-Whisper (雲端 API - 推薦)", "Local-Qwen3 (本地模型)"], 
                          index=0 if cur_stt == "Groq-Whisper" else 1)
    
    if "Local" in stt_engine:
        st.warning("⚠️ **Local-Qwen3 需求說明**")
        st.markdown("""
        1. **SoX 工具**: 必須安裝 SoX。 [點此下載 (SourceForge)](https://sourceforge.net/projects/sox/)
        2. **環境變數**: 將 `C:\\Program Files (x86)\\sox-14-4-2` (或您的安裝路徑) 加入系統的 **PATH**。
        3. **顯存需求**: 本地執行 1.7B 模型建議具備 **8GB VRAM**。
        4. **模型大小**: 首次執行將自動下載約 **4.5GB** 的檔案。
        """)

    if st.button("💾 儲育語音引擎設定"):
        engine_val = "Local-Qwen3" if "Local" in stt_engine else "Groq-Whisper"
        database.save_config("AUDIO_ENGINE", engine_val)
        st.success(f"已切換語音引擎為: {engine_val}")
        st.rerun()

    # --- 2026 模型規格參考 ---
    st.divider()
    st.header("📚 2026 Groq 模型規格與速率限制")
    
    model_data = {
        "模型名稱": [
            "meta-llama/llama-4-scout-17b-16e",
            "kimi-k2-instruct-0905",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ],
        "上下文 (Tokens)": ["128K", "256K", "128K", "128K"],
        "速率限制 (Free Tier)": [
            "30 RPM / 30,000 TPM",
            "15 RPM / 20,000 TPM",
            "30 RPM / 30,000 TPM",
            "30 RPM / 40,000 TPM"
        ],
        "圖像支援": ["✅ 原生多模態", "❌ 僅文字", "❌ 僅文字", "❌ 僅文字"],
        "建議用途": ["複雜推理+圖像", "超大型專案", "通用開發 (首選)", "極速轉譯"]
    }
    st.table(model_data)
    st.caption("註: RPM = 每分鐘請求數, TPM = 每分鐘 Token 數。快取命中的內容不計入 TPM。")

def handle_tpd_wait(wait_sec, error_msg):
    """處理 TPD 等待與倒數 UI。"""
    st.warning(f"🚨 觸發每日配額限制 (TPD)：{error_msg}")
    placeholder = st.empty()
    for i in range(wait_sec, 0, -1):
        placeholder.info(f"⏳ 系統將在 {i} 秒後自動重試...")
        time.sleep(1)
    placeholder.empty()
    st.success("✅ 配額已部分恢復，正在自動重試...")

def prd_generation_page():
    st.title("🎤 需求擷取與 PRD 生成")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. 輸入需求")
        audio_file = st.file_uploader("上傳需求音檔 (WAV/MP3)", type=["wav", "mp3"])
        
        if "transcribed_text" not in st.session_state:
            st.session_state["transcribed_text"] = ""

        if st.button("🎤 開始語音轉譯"):
            if audio_file:
                with st.spinner("Groq Whisper 正在轉譯..."):
                    with open("temp_audio.wav", "wb") as f:
                        f.write(audio_file.getbuffer())
                    raw_text = audio_engine.transcribe_audio("temp_audio.wav")
                    st.session_state["transcribed_text"] = raw_text
            else:
                st.warning("請先上傳音檔。")

        edited_text = st.text_area("需求初始描述 (或轉譯結果)", 
                                   value=st.session_state["transcribed_text"], 
                                   height=250)
        st.session_state["transcribed_text"] = edited_text

        if st.button("✨ 一鍵產出初步 PRD"):
            if edited_text:
                with st.spinner("Groq 正在規劃高品質 PRD..."):
                    while True:
                        prd_content = llm_service.generate_prd(edited_text)
                        if isinstance(prd_content, str) and prd_content.startswith("WAIT_REQUIRED"):
                            _, wait_sec, err = prd_content.split(":", 2)
                            handle_tpd_wait(int(wait_sec), err)
                            continue
                        st.session_state["current_prd"] = prd_content
                        break
            else:
                st.warning("需求內容不可為空。")

    with col2:
        st.subheader("2. PRD 預覽與滾動式修正")
        if "current_prd" in st.session_state and st.session_state["current_prd"]:
            edited_prd = st.text_area("手動修正 PRD Markdown", value=st.session_state["current_prd"], height=450)
            st.session_state["current_prd"] = edited_prd
            
            with st.expander("👀 預覽 PRD 渲染結果"):
                st.markdown(edited_prd)
            
            feedback = st.text_input("📝 輸入修正指令 (如：增加登入功能)")
            if st.button("🪄 AI 自動更新 PRD"):
                with st.spinner("AI 正在同步更新..."):
                    while True:
                        updated_prd = llm_service.update_prd_with_feedback(edited_prd, feedback)
                        if isinstance(updated_prd, str) and updated_prd.startswith("WAIT_REQUIRED"):
                            _, wait_sec, err = updated_prd.split(":", 2)
                            handle_tpd_wait(int(wait_sec), err)
                            continue
                        st.session_state["current_prd"] = updated_prd
                        st.rerun()
                        break
            
            st.divider()
            if st.button("🚀 一鍵分段生成完整專案 (防截斷)"):
                prd_content = st.session_state["current_prd"]
                
                with st.status("🚀 啟動開發流水線...", expanded=True) as status:
                    # 1. 規劃架構
                    st.write("1️⃣ 正在規劃專案架構...")
                    while True:
                        skeleton = code_generator.generate_project_skeleton(prd_content)
                        if isinstance(skeleton, str) and skeleton.startswith("WAIT_REQUIRED"):
                            _, wait_sec, err = skeleton.split(":", 2)
                            handle_tpd_wait(int(wait_sec), err)
                            continue
                        if not skeleton:
                            st.error("規劃失敗，AI 未能產出有效架構。")
                            return
                        break
                    
                    total = len(skeleton)
                    # 2. 規劃介面合約
                    st.write(f"2️⃣ 正在定義全域合約 (共 {total} 個檔案)...")
                    while True:
                        interface_map = code_generator.generate_interface_map(prd_content, skeleton)
                        if isinstance(interface_map, str) and interface_map.startswith("WAIT_REQUIRED"):
                            _, wait_sec, err = interface_map.split(":", 2)
                            handle_tpd_wait(int(wait_sec), err)
                            continue
                        break
                    
                    p_name = "New-Project"
                    p_path = file_worker.init_project_dir(p_name)
                    
                    # 3. 逐檔生成 (優化進度顯示)
                    pb = st.progress(0, text="準備填充代碼...")
                    for i, file_path in enumerate(skeleton):
                        progress_text = f"3️⃣ 開發中 ({i+1}/{total}): `{file_path}`"
                        pb.progress((i + 1) / total, text=progress_text)
                        
                        while True:
                            content = code_generator.generate_file_content(prd_content, file_path, skeleton, interface_map)
                            if isinstance(content, str) and content.startswith("WAIT_REQUIRED"):
                                _, wait_sec, err = content.split(":", 2)
                                handle_tpd_wait(int(wait_sec), err)
                                continue
                            file_worker.write_single_file(p_path, file_path, content)
                            break
                        time.sleep(3)

                    database.create_project(p_name, p_path)
                    status.update(label="✅ 完成！", state="complete", expanded=False)
                    st.success(f"專案已建立在: `{p_path}`")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
        else:
            st.info("請在左側輸入您的想法或上傳音檔開始。")

def project_overview_page():
    st.title("🏗️ 專案開發中心")
    projects = database.get_all_projects()
    if not projects:
        st.info("目前尚無專案，請先前往『需求擷取』產出專案。")
        return

    selected_project = st.selectbox("切換專案", projects, format_func=lambda x: f"{x[1]} ({x[3]})")
    if not selected_project: return
    p_id, p_name, p_path, _ = selected_project

    chat_key = f"chat_history_{p_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.header("📄 檔案瀏覽與編輯")
        all_files = []
        for root, _, files in os.walk(p_path):
            for file in files:
                all_files.append(os.path.relpath(os.path.join(root, file), p_path))
        
        selected_file = st.selectbox("選擇檔案", all_files, key=f"file_sel_{p_id}")
        if selected_file:
            content = file_worker.get_project_file_content(p_path, selected_file)
            edit_mode = st.toggle("✏️ 進入編輯模式", key=f"edit_toggle_{selected_file}")
            
            if edit_mode:
                new_code = st.text_area("Source Editor", value=content, height=600, key=f"editor_{selected_file}")
                if st.button("💾 儲存變更", key=f"save_{selected_file}"):
                    file_worker.update_specific_file(p_path, selected_file, new_code)
                    st.success("檔案已手動儲存。")
                    st.rerun()
            else:
                st.code(content, language="python" if selected_file.endswith(".py") else "markdown")

    with col_right:
        st.header("🤖 AI 專案助手")
        st.caption("您可以貼上報錯 Log，或直接描述修改需求。")

        chat_container = st.container(height=500)
        with chat_container:
            for msg in st.session_state[chat_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if prompt := st.chat_input("輸入指令 (例如：幫我新增一個健康檢查 API)"):
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            st.session_state[chat_key].append({"role": "user", "content": prompt})
            
            with st.spinner("AI 正在思考並執行變更..."):
                time.sleep(2)
                while True:
                    result = llm_service.fix_project_globally(p_path, st.session_state[chat_key])
                    ai_msg = result.get("message", "執行完成。")
                    
                    if ai_msg.startswith("WAIT_REQUIRED"):
                        _, wait_sec, err = ai_msg.split(":", 2)
                        handle_tpd_wait(int(wait_sec), err)
                        continue
                    
                    changes = result.get("changes", [])
                    if changes:
                        change_details = "\n\n**已套用以下變更：**"
                        for c in changes:
                            file_worker.write_single_file(p_path, c['path'], c['content'])
                            change_details += f"\n- `{c['action']}`: `{c['path']}`"
                        ai_msg += change_details

                    with chat_container:
                        with st.chat_message("assistant"):
                            st.markdown(ai_msg)
                    st.session_state[chat_key].append({"role": "assistant", "content": ai_msg})
                    st.rerun()
                    break

def main():
    st.sidebar.title("V2C: Groq 自動開發系統")
    page = st.sidebar.radio("導航", ["需求擷取", "專案總覽", "設定系統"])
    if page == "需求擷取": prd_generation_page()
    elif page == "設定系統": settings_page()
    elif page == "專案總覽": project_overview_page()

if __name__ == "__main__":
    main()
