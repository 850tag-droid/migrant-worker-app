import streamlit as st
import pandas as pd
import os
import json
import datetime
import google.generativeai as genai

# 1. 系統網頁基本設定
st.set_page_config(page_title="移工智慧實務智庫", layout="wide", initial_sidebar_state="expanded")
st.title("💼 移工智慧實務智庫系統")

DB_FILE = "database.csv"
COLUMNS = ["ID", "日期", "主題", "相關法規", "實務解決方案", "仲介常見行話", "狀態"]

# 初始化資料庫檔案
if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=COLUMNS)
    df_init.to_csv(DB_FILE, index=False)

# 讀取最新資料
df = pd.read_csv(DB_FILE)
df = df.astype(str).replace("nan", "")

# 側邊欄：設定 AI 大腦金鑰
st.sidebar.header("🔑 核心系統設定")
api_key = st.sidebar.text_input("請輸入 Gemini API Key", type="password", help="請至 Google AI Studio 免費申請")

# 主介面：三大分頁規劃
tab1, tab2, tab3 = st.tabs(["🔍 智庫檢索與快速查閱", "🤖 AI 社群對話過濾解析", "🛠️ 智庫資料編修與備份"])

# ==========================================
# Tab 1: 智庫檢索與快速查閱
# ==========================================
with tab1:
    st.header("🔍 全局關鍵字智慧檢索")
    search_query = st.text_input("請輸入關鍵字（例如：巴氏量表、洗工、廢聘...）", placeholder="點擊此處輸入...")

    # 篩選有效資料（排除已被徹底刪除的，保留有效與過時標記）
    display_df = df[df["狀態"] != "已刪除"]

    if search_query:
        mask = display_df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
        search_results = display_df[mask]
    else:
        search_results = display_df

    st.write(f"📊 目前檢索到 {len(search_results)} 筆相關知識點")
    st.write("---")

    # 大卡片美化輸出
    for _, row in search_results.iterrows():
        # 根據狀態決定標題樣式
        is_outdated = row["狀態"] == "過時標記"
        title_suffix = " ⚠️ (此對話主題已被標記為：過時知識)" if is_outdated else ""
        
        with st.container():
            st.subheader(f"📌 主題：{row['主題']}{title_suffix}")
            
            c1, c2, c3 = st.columns([1, 1, 2])
            c1.caption(f"📅 討論日期：{row['日期']}")
            c2.caption(f"💬 狀態：{row['狀態']}")
            if row['仲介常見行話']:
                c3.warning(f"🏷️ 仲介行話解密：{row['仲介常見行話']}")
            
            st.info(f"📜 **相關法規依據：**\n{row['相關法規']}")
            st.success(f"💡 **實務解決方案／對策：**\n{row['實務解決方案']}")
            st.write("---")

# ==========================================
# Tab 2: AI 社群對話過濾解析 (Human-in-the-loop)
# ==========================================
with tab2:
    st.header("🤖 LINE 社群對話大數據自動提煉")
    st.write("將 LINE 社群導出的純文字紀錄貼在下方，AI 將自動過濾閒聊，提煉高價值法令實務。")
    
    # 3. 日期區段分析選項
    col_d1, col_d2 = st.columns(2)
    start_date = col_d1.date_input("請選擇分析【開始日期】", datetime.date(2026, 1, 1))
    end_date = col_d2.date_input("請選擇分析【結束日期】", datetime.date(2026, 12, 31))

    raw_chat = st.text_area("📋 請在此處貼上 LINE 社群對話文字", height=250, placeholder="[LINE] 群組對話紀錄...")

    if st.button("🚀 開始進行智慧過濾分析"):
        if not api_key:
            st.error("❌ 請先在左側邊欄填入您的 Gemini API Key 才能啟動 AI 功能！")
        elif not raw_chat.strip():
            st.error("❌ 請輸入對話內容！")
        else:
            with st.spinner("AI 正在過濾垃圾訊息並分析法規對策中，請稍候..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # 精準定義 5 大欄位的 Prompt
                    prompt = f"""
                    你是一位精通台灣外籍移工引進法規、就業服務法與仲介實務對應的專家。
                    請分析以下 LINE 社群對話，並且「只擷取」發生在 {start_date} 到 {end_date} 之間的有效討論資訊。
                    
                    請嚴格過濾無意義的打招呼、貼圖、閒聊、以及與移工法令/實務無關的對話。
                    請將留下來的精華主題，精準整理成一個 JSON 陣列，格式必須嚴格符合以下欄位名稱，不要自創欄位：
                    [
                      {{
                        "日期": "對話發生的真實日期，格式統一為 YYYY/MM/DD",
                        "主題": "這段討論的核心業務主旨",
                        "相關法規": "涉及的條文法規、就業服務法條號、或勞動部最新函釋（若完全無提及法規，請寫：實務操作慣例）",
                        "實務解決方案": "針對此對話內提出的疑問，老手仲介或法令給出的具體操作建議與解決實務對策",
                        "仲介常見行話": "解密對話中出現的術語（例如：洗工、廢聘、巴氏、3年期滿，若無則留空）"
                      }}
                    ]
                    
                    對話紀錄如下：
                    {raw_chat}
                    
                    請直接輸出 JSON 陣列，絕對不要包含任何 markdown 標籤（如 ```json）或任何前言與結尾解釋。
                    """
                    response = model.generate_content(prompt)
                    clean_json = response.text.strip()
                    
                    # 存入 Session state 供人工確認機制使用
                    st.session_state["parsed_data"] = json.loads(clean_json)
                    st.success("✨ AI 分析完畢！請在下方進行【人工審查確認】。")
                except Exception as e:
                    st.error(f"分析失敗，錯誤訊息：{e}")

    # 1. 人工確認機制 (Human-in-the-loop)
    if "parsed_data" in st.session_state and st.session_state["parsed_data"]:
        st.write("---")
        st.subheader("👀 人工審查確認面板 (Human-in-the-loop)")
        st.write("以下為 AI 幫您初步提煉的結構化資訊，請確認或修改後再正式寫入您的智庫：")
        
        verified_list = []
        for i, item in enumerate(st.session_state["parsed_data"]):
            with st.expander(f"待確認知識點 #{i+1}：{item.get('主題', '未命名主題')}", expanded=True):
                v_date = st.text_input(f"日期 #{i+1}", item.get("日期", ""), key=f"d_{i}")
                v_topic = st.text_input(f"主題 #{i+1}", item.get("主題", ""), key=f"t_{i}")
                v_law = st.text_area(f"相關法規依據 #{i+1}", item.get("相關法規", ""), key=f"l_{i}")
                v_sol = st.text_area(f"實務解決方案/對策 #{i+1}", item.get("實務解決方案", ""), key=f"s_{i}")
                v_jargon = st.text_input(f"仲介常見行話解密 #{i+1}", item.get("仲介常見行話", ""), key=f"j_{i}")
                
                verified_list.append({
                    "ID": str(int(datetime.datetime.now().timestamp()) + i),
                    "日期": v_date,
                    "主題": v_topic,
                    "相關法規": v_law,
                    "實務解決方案": v_sol,
                    "仲介常見行話": v_jargon,
                    "狀態": "有效"
                })
        
        if st.button("💾 檢查無誤，正式寫入智慧智庫資料庫"):
            new_df = pd.DataFrame(verified_list)
            df = pd.concat([df, new_df], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.session_state["parsed_data"] = None
            st.success("🎉 資料已成功寫入智庫！請前往【智庫檢索】分頁查閱。")
            st.rerun()

# ==========================================
# Tab 3: 智庫資料編修與備份 (手動編修、過時與刪除)
# ==========================================
with tab3:
    st.header("🛠️ 智庫資料維護與手動編修後台")
    
    # 3 & 4. 手動編修、標記過時、刪除功能
    if df.empty or len(df[df["狀態"] != "已刪除"]) == 0:
        st.info("目前資料庫內尚無有效數據可供編修。")
    else:
        active_df = df[df["狀態"] != "已刪除"]
        edit_target = st.selectbox("🎯 請選取您想要編輯或處置的知識點主題：", active_df["主題"].unique())
        
        target_row = active_df[active_df["主題"] == edit_target].iloc[0]
        target_idx = df[df["主題"] == edit_target].index[0]
        
        with st.form("manual_edit_form"):
            st.write(f"📝 正在編輯知識點 ID: {target_row['ID']}")
            ed_date = st.text_input("✍️ 修改日期", target_row["日期"])
            ed_topic = st.text_input("✍️ 修改主題名稱", target_row["主題"])
            ed_law = st.text_area("✍️ 修改相關法規", target_row["相關法規"])
            ed_sol = st.text_area("✍️ 修改實務解決方案", target_row["實務解決方案"])
            ed_jargon = st.text_input("✍️ 修改仲介常見行話", target_row["仲介常見行話"])
            ed_status = st.selectbox("🚨 變更知識有效狀態", ["有效", "過時標記", "已刪除"], 
                                     index=["有效", "過時標記", "已刪除"].index(target_row["狀態"]))
            
            btn_save = st.form_submit_button("💾 儲存修改內容")
            
            if btn_save:
                df.at[target_idx, "日期"] = ed_date
                df.at[target_idx, "主題"] = ed_topic
                df.at[target_idx, "相關法規"] = ed_law
                df.at[target_idx, "實務解決方案"] = ed_sol
                df.at[target_idx, "仲介常見行話"] = ed_jargon
                df.at[target_idx, "狀態"] = ed_status
                df.to_csv(DB_FILE, index=False)
                st.success("✅ 智庫數據已手動編修完成！系統已同步重啟更新。")
                st.rerun()

    st.write("---")
    st.subheader("📥 2. 智庫核心數據安全備份區")
    st.write("由於免費雲端主機重啟時會清空暫存資料，建議您每次大量新增或修改智庫後，點擊下方按鈕將大資料庫下載回電腦備份。")
    
    # 輸出成 CSV 下載按鈕
    csv_buffer = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下載最新智慧智庫備份檔 (database.csv)",
        data=csv_buffer,
        file_name="migrant_worker_backup.csv",
        mime="text/csv"
    )