import streamlit as st
import pandas as pd
import json
import datetime
import io
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. 網頁基本設定
st.set_page_config(page_title="人力仲介知識系統", layout="wide", initial_sidebar_state="expanded")

# 2. 安全驗證：從雲端保險箱讀取密碼與設定
try:
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
    USER_PWD = st.secrets["USER_PASSWORD"]
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    DRIVE_FOLDER_ID = st.secrets["DRIVE_FOLDER_ID"]
    GOOGLE_JSON_DICT = json.loads(st.secrets["GOOGLE_JSON"])
except Exception as e:
    st.error("❌ 系統保險箱 (Secrets) 設定不完整，請檢查 Streamlit 後台設定！")
    st.stop()

# 3. 初始化登入狀態
if "login_status" not in st.session_state:
    st.session_state["login_status"] = False
    st.session_state["user_role"] = None

# ---- 🔍 登入攔截畫面 ----
if not st.session_state["login_status"]:
    st.title("🔐 人力仲介知識系統 - 安全登入")
    with st.form("login_form"):
        username = st.text_input("請輸入帳號", placeholder="admin 或 user")
        password = st.text_input("請輸入密碼", type="password")
        btn_login = st.form_submit_button("確認登入")
        
        if btn_login:
            if username == "admin" and password == ADMIN_PWD:
                st.session_state["login_status"] = True
                st.session_state["user_role"] = "管理員"
                st.rerun()
            elif username == "user" and password == USER_PWD:
                st.session_state["login_status"] = True
                st.session_state["user_role"] = "一般使用者"
                st.rerun()
            else:
                st.error("❌ 帳號或密碼錯誤，請重新輸入！")
    st.stop()

# ---- 🔓 核心系統區 (已登入) ----

# 4. 連線 Google 雙棲服務 (Sheets & Drive)
@st.cache_resource(ttl=60)
def connect_google_services():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]
    creds = Credentials.from_service_account_info(GOOGLE_JSON_DICT, scopes=scopes)
    
    # 試算表連線
    client_sheets = gspread.authorize(creds)
    sheet_url = "https://docs.google.com/spreadsheets/d/1RyY0kOi09pydOo-xxTd9UGnLEujHm6Z6wc2R9hG4hLw/edit?usp=drive_link" 
    wks = client_sheets.open_by_url(sheet_url).sheet1
    
    # 雲端硬碟連線
    service_drive = build('drive', 'v3', credentials=creds)
    return wks, service_drive

try:
    wks, drive_service = connect_google_services()
    records = wks.get_all_records()
    df = pd.DataFrame(records) if records else pd.DataFrame(columns=["ID", "日期", "主題", "相關法規", "實務解決方案", "仲介常見行話", "狀態", "附件連結"])
    df = df.astype(str).replace("nan", "")
except Exception as e:
    st.error(f"❌ 無法連線至 Google 服務，請確認共用設定！錯誤原因: {e}")
    st.stop()

# 頂部狀態列
c_title, c_logout = st.columns([9, 1])
c_title.title(f"💼 人力仲介知識系統 ({st.session_state['user_role']}模式)")
if c_logout.button("🚪 登出系統"):
    st.session_state["login_status"] = False
    st.session_state["user_role"] = None
    st.rerun()

# 權限分流顯示分頁
if st.session_state["user_role"] == "管理員":
    tab1, tab2, tab3 = st.tabs(["🔍 智庫檢索與快速查閱", "🤖 AI 對話智慧解析", "🛠️ 智庫維護與附件上傳"])
else:
    tab1 = st.tabs(["🔍 智庫檢索與快速查閱"])[0]
    tab2, tab3 = None, None

# ==========================================
# Tab 1: 智庫檢索與快速查閱 (所有人)
# ==========================================
with tab1:
    st.header("🔍 全局關鍵字智慧檢索")
    search_query = st.text_input("請輸入關鍵字（多關鍵字請用「空白」隔開）", placeholder="例如：越南 駕照")
    display_df = df[df["狀態"] != "已刪除"] if not df.empty else df

    if search_query and not display_df.empty:
        keywords = search_query.split()
        mask = display_df.apply(lambda row: all(kw.lower() in " ".join(row.astype(str)).lower() for kw in keywords), axis=1)
        search_results = display_df[mask]
    else:
        search_results = display_df

    st.write(f"📊 檢索到 {len(search_results)} 筆結果")
    st.write("---")

    for _, row in search_results.iterrows():
        is_outdated = row["狀態"] == "過時標記"
        title_suffix = " ⚠️ (過時知識)" if is_outdated else ""
        
        with st.container():
            st.subheader(f"📌 {row['主題']}{title_suffix}")
            c1, c2, c3 = st.columns([1, 1, 2])
            c1.caption(f"📅 日期：{row['日期']}")
            c2.caption(f"💬 狀態：{row['狀態']}")
            if row.get('仲介常見行話'):
                c3.warning(f"🏷️ 行話：{row['仲介常見行話']}")
            
            st.info(f"📜 **相關法規：**\n{row['相關法規']}")
            st.success(f"💡 **實務解決方案：**\n{row['實務解決方案']}")
            
            # 若有附件則顯示下載按鈕
            if row.get('附件連結') and str(row['附件連結']).startswith('http'):
                st.markdown(f"**📎 [點擊檢視 / 下載雲端附件]({row['附件連結']})**")
            st.write("---")

# ==========================================
# Tab 2: AI 對話智慧解析 (僅管理員)
# ==========================================
if tab2:
    with tab2:
        st.header("🤖 LINE 對話大數據自動提煉")
        c_d1, c_d2 = st.columns(2)
        start_date = c_d1.date_input("分析開始日期", datetime.date(2026, 1, 1))
        end_date = c_d2.date_input("分析結束日期", datetime.date(2026, 12, 31))
        raw_chat = st.text_area("📋 貼上 LINE 對話", height=200)

        if st.button("🚀 啟動 AI 提煉"):
            if raw_chat.strip():
                with st.spinner("AI 運算中，請稍候..."):
                    try:
                        genai.configure(api_key=GEMINI_KEY)
                        model = genai.GenerativeModel('gemini-3.5-flash')
                        prompt = f"""請分析以下對話，過濾閒聊，擷取 {start_date} 到 {end_date} 之間的有效實務。
                        輸出嚴格 JSON 陣列：[{{"日期":"YYYY/MM/DD", "主題":"", "相關法規":"", "實務解決方案":"", "仲介常見行話":""}}]
                        對話：{raw_chat}"""
                        response = model.generate_content(prompt)
                        st.session_state["parsed_data"] = json.loads(response.text.strip())
                        st.success("✨ 分析完畢！請在下方進行人工審核。")
                    except Exception as e:
                        st.error(f"分析失敗: {e}")

        if "parsed_data" in st.session_state and st.session_state["parsed_data"]:
            st.write("---")
            verified_list = []
            for i, item in enumerate(st.session_state["parsed_data"]):
                with st.expander(f"待確認 #{i+1}：{item.get('主題', '')}", expanded=True):
                    v_date = st.text_input(f"日期 #{i+1}", item.get("日期", ""))
                    v_topic = st.text_input(f"主題 #{i+1}", item.get("主題", ""))
                    v_law = st.text_area(f"法規 #{i+1}", item.get("相關法規", ""))
                    v_sol = st.text_area(f"對策 #{i+1}", item.get("實務解決方案", ""))
                    v_jargon = st.text_input(f"行話 #{i+1}", item.get("仲介常見行話", ""))
                    
                    verified_list.append([
                        str(int(datetime.datetime.now().timestamp()) + i),
                        v_date, v_topic, v_law, v_sol, v_jargon, "有效", "" 
                    ])
            if st.button("💾 確認無誤，寫入資料庫"):
                for row_data in verified_list:
                    wks.append_row(row_data)
                st.session_state["parsed_data"] = None
                st.cache_resource.clear()
                st.rerun()

# ==========================================
# Tab 3: 智庫維護與附件上傳 (僅管理員)
# ==========================================
if tab3:
    with tab3:
        st.header("🛠️ 後台維護與建檔中心")
        
        # 區塊 A：新增與上傳
        with st.expander("➕ 手動新增實務知識與上傳附件", expanded=True):
            with st.form("manual_add_form", clear_on_submit=True):
                n_date = st.date_input("日期", datetime.date.today())
                n_topic = st.text_input("主題 (必填)")
                n_law = st.text_area("相關法規")
                n_sol = st.text_area("實務解決方案")
                n_jargon = st.text_input("常見行話")
                
                st.write("📎 **上傳參考附件 (自動存入 Google Drive 📂人力仲介知識系統)**")
                uploaded_file = st.file_uploader("選擇檔案 (PDF, Word, 圖片)", type=["pdf", "doc", "docx", "jpg", "png", "jpeg"])
                
                if st.form_submit_button("💾 新增並上傳") and n_topic:
                    file_link = ""
                    if uploaded_file:
                        with st.spinner("檔案上傳中..."):
                            file_meta = {'name': uploaded_file.name, 'parents': [DRIVE_FOLDER_ID]}
                            media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type, resumable=True)
                            file_drive = drive_service.files().create(body=file_meta, media_body=media, fields='id, webViewLink').execute()
                            drive_service.permissions().create(fileId=file_drive.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
                            file_link = file_drive.get('webViewLink')
                            st.success("✅ 附件上傳成功！")

                    new_id = str(int(datetime.datetime.now().timestamp()))
                    wks.append_row([new_id, str(n_date), n_topic, n_law, n_sol, n_jargon, "有效", file_link])
                    st.success("🎉 資料建檔完成！")
                    st.cache_resource.clear()
                    st.rerun()

        st.write("---")
        
        # 區塊 B：修改與刪除
        st.subheader("📝 編輯現現有資料")
        active_df = df[df["狀態"] != "已刪除"] if not df.empty else df
        if active_df.empty:
            st.info("目前無資料。")
        else:
            edit_target = st.selectbox("🎯 選取要編輯的主題：", active_df["主題"].unique())
            target_idx = df[df["主題"] == edit_target].index[0]
            target_row = df.iloc[target_idx]
            sheet_row_num = int(target_idx) + 2 
            
            with st.form("manual_edit_form"):
                e_date = st.text_input("✍️ 修改日期", target_row["日期"])
                e_topic = st.text_input("✍️ 修改主題", target_row["主題"])
                e_law = st.text_area("✍️ 修改法規", target_row["相關法規"])
                e_sol = st.text_area("✍️ 修改對策", target_row["實務解決方案"])
                e_jargon = st.text_input("✍️ 修改行話", target_row["仲介常見行話"])
                e_status = st.selectbox("🚨 狀態", ["有效", "過時標記", "已刪除"], index=["有效", "過時標記", "已刪除"].index(target_row["狀態"]))
                e_link = st.text_input("🔗 附件網址", target_row.get("附件連結", ""))
                
                if st.form_submit_button("💾 儲存修改"):
                    wks.update_cell(sheet_row_num, 2, e_date)
                    wks.update_cell(sheet_row_num, 3, e_topic)
                    wks.update_cell(sheet_row_num, 4, e_law)
                    wks.update_cell(sheet_row_num, 5, e_sol)
                    wks.update_cell(sheet_row_num, 6, e_jargon)
                    wks.update_cell(sheet_row_num, 7, e_status)
                    wks.update_cell(sheet_row_num, 8, e_link)
                    st.success("✅ 修改完成！")
                    st.cache_resource.clear()
                    st.rerun()
