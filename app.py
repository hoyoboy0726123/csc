import streamlit as st
import os
import database
import audio_engine
import llm_service
import code_generator
import file_worker
from model_loader import load_model

# 頁面配置
st.set_page_config(page_title="AI 語音驅動全自動開發系統", layout="wide")

# 初始化資料庫
database.init_db()

def settings_page():
    st.title("⚙️ 全域主模型設定")
    st.markdown("請設定系統的主模型。整個開發流程（需求生成、程式碼產出、錯誤修復）將統一使用此配置。")

    # 讀取目前設定
    cur_provider = database.get_config("ACTIVE_PROVIDER", "Gemini")
    cur_key = database.get_config("ACTIVE_KEY", "")
    cur_model = database.get_config("ACTIVE_MODEL", "")

    st.divider()

    # 1. 供應商選擇
    provider = st.radio("1. 選擇 AI 供應商", ["Gemini", "Groq"], index=0 if cur_provider == "Gemini" else 1)
    
    # 2. 金鑰輸入
    api_key = st.text_input(f"2. 輸入 {provider} API Key", value=cur_key, type="password")
    
    # 3. 模型選擇 (動態獲取)
    model_options = []
    if api_key:
        with st.spinner(f"正在連線 {provider} 獲取可用模型..."):
            model_options = llm_service.get_dynamic_models(provider, api_key)
    
    if not model_options:
        # 預設選項
        model_options = ["gemini-2.0-flash", "gemini-1.5-flash"] if provider == "Gemini" else ["llama-3.3-70b-versatile"]

    selected_model = st.selectbox("3. 選擇主模型", options=model_options, 
                                  index=model_options.index(cur_model) if cur_model in model_options else 0)

    st.divider()

    # 測試與儲存
    if st.button("🚀 測試並儲存全域設定"):
        if not api_key:
            st.error("請輸入 API Key。")
        else:
            with st.spinner("正在測試 API 連線..."):
                success, msg = llm_service.test_connection(provider, api_key, selected_model)
                if success:
                    database.save_config("ACTIVE_PROVIDER", provider)
                    database.save_config("ACTIVE_KEY", api_key)
                    database.save_config("ACTIVE_MODEL", selected_model)
                    st.success(f"連線成功！已將 {provider} / {selected_model} 設為全域主模型。")
                    st.rerun()
                else:
                    st.error(msg)

    # 顯示目前狀態
    st.info(f"🟢 **當前啟動中:** {cur_provider} ({cur_model})")

def prd_generation_page():
    st.title("🎤 語音/文字需求擷取")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. 輸入需求")
        audio_file = st.file_uploader("上傳音檔 (WAV/MP3)", type=["wav", "mp3"])
        raw_text_input = st.text_area("或者直接輸入需求內容", height=200)
        
        if st.button("✨ 開始生成 PRD"):
            raw_text = ""
            if audio_file:
                with st.spinner("正在轉譯語音..."):
                    with open("temp_audio.wav", "wb") as f:
                        f.write(audio_file.getbuffer())
                    raw_text = audio_engine.transcribe_audio("temp_audio.wav")
                    st.info(f"轉譯結果：{raw_text}")
            elif raw_text_input:
                raw_text = raw_text_input
            
            if raw_text:
                with st.spinner("AI 正在規劃 PRD..."):
                    prd_content = llm_service.generate_prd(raw_text)
                    st.session_state["current_prd"] = prd_content
            else:
                st.warning("請提供音檔或文字。")

    with col2:
        st.subheader("2. PRD 預覽與修正")
        if "current_prd" in st.session_state:
            st.markdown(st.session_state["current_prd"])
            
            feedback = st.text_input("輸入修正建議")
            if st.button("更新 PRD"):
                with st.spinner("正在更新..."):
                    updated_prd = llm_service.update_prd_with_feedback(st.session_state["current_prd"], feedback)
                    st.session_state["current_prd"] = updated_prd
                    st.rerun()
            
            st.divider()
            if st.button("🚀 一鍵分段生成完整專案 (防截斷)"):
                prd_content = st.session_state["current_prd"]
                
                # 1. 規劃架構
                with st.status("正在規劃專案架構...", expanded=True) as status:
                    skeleton = code_generator.generate_project_skeleton(prd_content)
                    if not skeleton:
                        st.error("無法規劃架構，請檢查 API 設定。")
                    else:
                        st.write(f"預計生成 {len(skeleton)} 個檔案...")
                        
                        # 2. 初始化目錄
                        p_name = "New-Project"
                        p_path = file_worker.init_project_dir(p_name)
                        
                        # 3. 逐檔生成
                        progress_bar = st.progress(0)
                        for i, file_path in enumerate(skeleton):
                            st.write(f"正在填充: `{file_path}` ...")
                            content = code_generator.generate_file_content(prd_content, file_path, skeleton)
                            file_worker.write_single_file(p_path, file_path, content)
                            progress_bar.progress((i + 1) / len(skeleton))
                        
                        # 4. 完成
                        database.create_project(p_name, p_path)
                        status.update(label="✅ 專案生成完成！", state="complete", expanded=False)
                        st.success(f"專案已建立在: `{p_path}`")
                        st.balloons()
        else:
            st.info("尚未生成內容。")

def project_overview_page():
    st.title("📂 專案檔案總覽")
    projects = database.get_all_projects()
    if not projects:
        st.info("尚無專案。")
        return

    selected_project = st.selectbox("選擇專案", projects, format_func=lambda x: f"{x[1]} ({x[3]})")
    if selected_project:
        _, _, p_path, _ = selected_project
        all_files = []
        for root, _, files in os.walk(p_path):
            for file in files:
                all_files.append(os.path.relpath(os.path.join(root, file), p_path))
        
        selected_file = st.selectbox("檢視檔案", all_files)
        if selected_file:
            content = file_worker.get_project_file_content(p_path, selected_file)
            st.code(content, language="python" if selected_file.endswith(".py") else "markdown")
            
            st.divider()
            st.subheader("🛠️ 自動修復")
            error_log = st.text_area("貼上錯誤 Log", height=100)
            if st.button("修復檔案"):
                with st.spinner("AI 修復中..."):
                    fixed = llm_service.fix_code_error(content, error_log)
                    file_worker.update_specific_file(p_path, selected_file, fixed)
                    st.success("已修復！")
                    st.rerun()

def main():
    st.sidebar.title("AI 自動開發系統")
    page = st.sidebar.radio("導航", ["需求擷取", "專案總覽", "設定主模型"])
    if page == "需求擷取": prd_generation_page()
    elif page == "設定主模型": settings_page()
    elif page == "專案總覽": project_overview_page()

if __name__ == "__main__":
    main()
