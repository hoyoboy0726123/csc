import streamlit as st
import os
import time
import database
import audio_engine
import llm_service
import code_generator
import file_worker
from streamlit_mic_recorder import mic_recorder

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
    api_key = st.text_input("1. 輸入 Groq API Key", value=cur_key, type="password")
    
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
        1. **SoX 工具**: 必須安裝 SoX。 [點此下載](https://sourceforge.net/projects/sox/)
        2. **環境變數**: 將 `sox` 路徑加入系統 **PATH**。
        3. **模型大小**: 約 4.5GB。
        """)

    if st.button("💾 儲存語音引擎設定"):
        engine_val = "Local-Qwen3" if "Local" in stt_engine else "Groq-Whisper"
        database.save_config("AUDIO_ENGINE", engine_val)
        st.success(f"已切換語音引擎為: {engine_val}")
        st.rerun()

    # 模型規格表
    st.divider()
    st.header("📚 2026 Groq 模型規格")
    model_data = {
        "模型名稱": ["meta-llama/llama-4-scout-17b-16e", "kimi-k2-instruct-0905", "llama-3.3-70b-versatile"],
        "上下文 (Tokens)": ["128K", "256K", "128K"],
        "速率限制 (Free)": ["30 RPM", "15 RPM", "30 RPM"],
        "特色": ["✅ 原生多模態", "✅ 256K 超長上下文", "✅ 邏輯穩定 (首選)"]
    }
    st.table(model_data)

def handle_tpd_wait(wait_sec, error_msg):
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
        
        # --- 簡單錄音功能 ---
        st.write("點擊按鈕開始錄製需求 (結束後自動轉錄)：")
        audio = mic_recorder(
            start_prompt="⏺️ 開始錄音",
            stop_prompt="⏹️ 停止並轉錄",
            just_once=True,
            use_container_width=True,
            key='simple_recorder'
        )

        if "transcribed_text" not in st.session_state:
            st.session_state["transcribed_text"] = ""

        if audio:
            with st.spinner("正在識別繁體中文..."):
                with open("temp_audio.wav", "wb") as f:
                    f.write(audio['bytes'])
                raw_text = audio_engine.transcribe_audio("temp_audio.wav")
                st.session_state["transcribed_text"] = raw_text
                st.success("✅ 轉錄完成！")

        uploaded_file = st.file_uploader("或上傳音檔 (WAV/MP3)", type=["wav", "mp3"])
        if uploaded_file and st.button("⚡ 轉譯上傳的音檔"):
            with st.spinner("轉譯中..."):
                with open("temp_audio.wav", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.session_state["transcribed_text"] = audio_engine.transcribe_audio("temp_audio.wav")

        st.divider()
        # 支援手動編輯
        edited_text = st.text_area("需求描述原始文字 (轉錄後可在此進行最終修正)", 
                                   value=st.session_state["transcribed_text"], 
                                   height=300)
        st.session_state["transcribed_text"] = edited_text

        if st.button("✨ 產出高品質 PRD (AI 會自動過濾雜訊)"):
            if edited_text:
                with st.spinner("AI 正在分析核心需求並規劃 PRD..."):
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
        st.subheader("2. PRD 預覽與修正")
        if "current_prd" in st.session_state and st.session_state["current_prd"]:
            edited_prd = st.text_area("手動修正 PRD Markdown", value=st.session_state["current_prd"], height=450)
            st.session_state["current_prd"] = edited_prd
            with st.expander("👀 預覽 PRD 渲染結果"):
                st.markdown(edited_prd)
            
            feedback = st.text_input("📝 輸入修正指令")
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
                    st.write("1️⃣ 規劃架構...")
                    while True:
                        skeleton = code_generator.generate_project_skeleton(prd_content)
                        if isinstance(skeleton, str) and skeleton.startswith("WAIT_REQUIRED"):
                            _, wait_sec, err = skeleton.split(":", 2)
                            handle_tpd_wait(int(wait_sec), err)
                            continue
                        break
                    
                    total = len(skeleton)
                    st.write(f"2️⃣ 定義合約 (共 {total} 個檔案)...")
                    while True:
                        interface_map = code_generator.generate_interface_map(prd_content, skeleton)
                        if isinstance(interface_map, str) and interface_map.startswith("WAIT_REQUIRED"):
                            _, wait_sec, err = interface_map.split(":", 2)
                            handle_tpd_wait(int(wait_sec), err)
                            continue
                        break
                    
                    p_path = file_worker.init_project_dir("New-Project")
                    pb = st.progress(0, text="填充代碼...")
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

                    database.create_project("New-Project", p_path)
                    status.update(label="✅ 完成！", state="complete", expanded=False)
                    st.success(f"專案已建立在: `{p_path}`")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
        else:
            st.info("請在左側輸入想法或錄音開始。")

def project_overview_page():
    st.title("🏗️ 專案開發中心")
    projects = database.get_all_projects()
    if not projects:
        st.info("目前尚無專案，請先前往『需求擷取』產出專案。")
        return

    selected_project = st.selectbox("切換專案", projects, format_func=lambda x: f"{x[1]} ({x[3]})")
    if not selected_project: return
    p_id, p_name, p_path, _ = selected_project

    with st.sidebar:
        st.divider()
        st.subheader("⚠️ 危險區域")
        if st.button("🗑️ 刪除目前專案", type="secondary"):
            st.session_state[f"confirm_delete_{p_id}"] = True
        if st.session_state.get(f"confirm_delete_{p_id}", False):
            st.error(f"確定要永久刪除『{p_name}』嗎？")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔴 確認刪除", type="primary"):
                    file_worker.delete_project_folder(p_path)
                    database.delete_project_record(p_id)
                    st.success("專案已徹底刪除。")
                    del st.session_state[f"confirm_delete_{p_id}"]
                    time.sleep(1)
                    st.rerun()
            with c2:
                if st.button("🔵 取消"):
                    del st.session_state[f"confirm_delete_{p_id}"]
                    st.rerun()

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
                    st.success("檔案已儲存。")
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

        if prompt := st.chat_input("輸入指令"):
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
                        for c in changes:
                            file_worker.write_single_file(p_path, c['path'], c['content'])
                        ai_msg += f"\n\n**已套用 {len(changes)} 個檔案變更。**"
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
