import streamlit as st
import pandas as pd
import datetime
import os
import io
import re
import json
from openai import OpenAI

# --- 1. 系統初始化與設定 ---
DB_FILE = "database.csv"

def init_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=[
            "id", "category", "keywords", "subject", "legal_basis", "description", "expiry_date", "source"
        ])
        df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame()

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")

init_db()

# 頁面配置
st.set_page_config(page_title="外籍移工智慧法令知識庫", layout="wide", initial_sidebar_state="collapsed")

# 自定義 CSS (大字體、高亮、警示燈)
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stTextInput input { font-size: 24px !important; padding: 20px !important; border-radius: 15px !important; }
    .dashboard-card {
        background-color: white; padding: 30px; border-radius: 20px; text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); cursor: pointer; transition: 0.3s; border: 1px solid #eee;
    }
    .dashboard-card:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.1); }
    .card-icon { font-size: 50px; margin-bottom: 15px; }
    .card-text { font-size: 20px; font-weight: bold; color: #333; }
    
    .search-result-card {
        background-color: white; padding: 25px; border-radius: 15px; border-left: 10px solid #007bff;
        margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .result-title { font-size: 26px; font-weight: bold; color: #1e3a8a; margin-bottom: 10px; }
    .result-meta { font-size: 16px; color: #666; margin-bottom: 15px; }
    .result-content { font-size: 20px; line-height: 1.6; color: #333; }
    .highlight { background-color: #ffeb3b; padding: 2px 5px; border-radius: 5px; font-weight: bold; }
    
    .status-dot { height: 15px; width: 15px; border-radius: 50%; display: inline-block; margin-right: 10px; }
    .dot-red { background-color: #ff4b4b; box-shadow: 0 0 10px #ff4b4b; }
    .dot-yellow { background-color: #ffa500; box-shadow: 0 0 10px #ffa500; }
    .alert-card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #eee; background: white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AI 解析模組 ---
def process_line_chat(api_key, text_content):
    client = OpenAI(api_key=api_key)
    prompt = f"""
    分析以下 LINE 聊天紀錄，過濾廢話，提取「法令與實務」知識。
    請輸出 JSON 格式列表，每個項目包含：
    category (法規動態/行話解密/實務個案/勞檢應對), keywords (核心關鍵字), 
    subject (社群口語), legal_basis (正式法規依據), description (完整說明與實務對策)
    
    內容：
    {text_content}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        res = json.loads(response.choices[0].message.content)
        return res.get("data", res) if isinstance(res, dict) else res
    except:
        return []

# --- 3. 頁面導航控制 ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def go_home(): st.session_state.page = 'home'
def go_alert(): st.session_state.page = 'alert'
def go_import(): st.session_state.page = 'import'
def go_list(): st.session_state.page = 'list'

# --- 4. 介面呈現 ---

# 頂部導航 (僅在非首頁顯示)
if st.session_state.page != 'home':
    if st.button("⬅️ 返回首頁"): go_home()

# 【首頁：大圖標儀表板】
if st.session_state.page == 'home':
    st.markdown("<h1 style='text-align: center; color: #1e3a8a; margin-bottom: 40px;'>外籍移工智慧法令知識庫</h1>", unsafe_allow_html=True)
    
    # 核心搜尋框
    search_query = st.text_input("", placeholder="🔍 輸入關鍵字搜尋（如：巴氏、洗工、聘可...）")
    
    if search_query:
        # 執行搜尋邏輯
        df = load_data()
        results = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
        
        st.write(f"找到 {len(results)} 筆結果")
        for _, row in results.iterrows():
            def hl(text): return re.sub(f"({re.escape(search_query)})", r'<span class="highlight">\1</span>', str(text), flags=re.IGNORECASE)
            st.markdown(f"""
                <div class="search-result-card">
                    <div class="result-title">{hl(row['subject'])}</div>
                    <div class="result-meta"><b>分類：</b>{row['category']} | <b>關鍵字：</b>{hl(row['keywords'])} | <b>法規：</b>{row['legal_basis']}</div>
                    <div class="result-content">{hl(row['description'])}</div>
                </div>
            """, unsafe_allow_html=True)
        st.divider()

    # 大圖標按鈕區
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔥 雙軌到期警示面板", key="btn_alert", help="查看即時效期預警"): go_alert()
        st.markdown('<div class="dashboard-card"><div class="card-icon">🚨</div><div class="card-text">雙軌到期警示</div></div>', unsafe_allow_html=True)
    with col2:
        if st.button("📥 LINE 紀錄自動匯入", key="btn_import"): go_import()
        st.markdown('<div class="dashboard-card"><div class="card-icon">📲</div><div class="card-text">LINE 紀錄匯入</div></div>', unsafe_allow_html=True)
    with col3:
        if st.button("📖 完整知識庫瀏覽", key="btn_list"): go_list()
        st.markdown('<div class="dashboard-card"><div class="card-icon">📚</div><div class="card-text">完整知識清單</div></div>', unsafe_allow_html=True)

# 【分頁：雙軌到期警示】
elif st.session_state.page == 'alert':
    st.title("🚨 雙軌到期警示面板")
    df = load_data()
    df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
    today = pd.Timestamp(datetime.date.today())
    
    red_alerts = df[df['expiry_date'] <= today + pd.Timedelta(days=60)]
    yellow_alerts = df[(df['expiry_date'] > today + pd.Timedelta(days=60)) & (df['expiry_date'] <= today + pd.Timedelta(days=120))]
    
    col_r, col_y = st.columns(2)
    with col_r:
        st.subheader("🔴 紅色緊急燈 (60天內)")
        for _, row in red_alerts.iterrows():
            st.markdown(f'<div class="alert-card"><span class="status-dot dot-red"></span><b>{row["subject"]}</b><br>到期日：{row["expiry_date"].date()}</div>', unsafe_allow_html=True)
    with col_y:
        st.subheader("🟡 黃色預警燈 (60-120天)")
        for _, row in yellow_alerts.iterrows():
            st.markdown(f'<div class="alert-card"><span class="status-dot dot-yellow"></span><b>{row["subject"]}</b><br>到期日：{row["expiry_date"].date()}</div>', unsafe_allow_html=True)

# 【分頁：LINE 紀錄自動匯入】
elif st.session_state.page == 'import':
    st.title("📥 LINE 紀錄自動匯入")
    uploaded_file = st.file_uploader("上傳 LINE 聊天紀錄 (.txt)", type="txt")
    api_key = st.text_input("輸入 AI API Key (OpenAI/Gemini)", type="password")
    
    if st.button("🚀 開始分析並匯入"):
        if uploaded_file and api_key:
            with st.spinner("AI 分析中..."):
                content = uploaded_file.read().decode("utf-8")
                new_data = process_line_chat(api_key, content[:10000])
                if new_data:
                    df = load_data()
                    for item in new_data:
                        item['id'] = len(df) + 1
                        item['source'] = "LINE Import"
                        item['expiry_date'] = (datetime.date.today() + datetime.timedelta(days=180)).isoformat()
                        df = pd.concat([df, pd.DataFrame([item])], ignore_index=True)
                    save_data(df)
                    st.success(f"成功匯入 {len(new_data)} 筆資料！")
        else:
            st.warning("請提供檔案與 API Key")

# 【分頁：完整知識庫瀏覽】
elif st.session_state.page == 'list':
    st.title("📖 完整知識庫清單")
    df = load_data()
    
    # 匯出按鈕
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 下載最新 CSV 資料庫", data=csv, file_name="knowledge_base.csv", mime="text/csv")
    
    st.dataframe(df, use_container_width=True)
    
    with st.expander("➕ 手動新增資料"):
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            cat = c1.selectbox("分類", ["法規動態", "行話解密", "實務個案", "勞檢應對"])
            sub = c2.text_input("主題")
            kw = st.text_input("關鍵字")
            legal = st.text_input("法規依據")
            desc = st.text_area("詳細說明")
            exp = st.date_input("提醒到期日", value=datetime.date.today() + datetime.timedelta(days=365))
            if st.form_submit_button("儲存"):
                new_row = {"id": len(df)+1, "category": cat, "keywords": kw, "subject": sub, 
                           "legal_basis": legal, "description": desc, "expiry_date": exp.isoformat(), "source": "Manual"}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("已儲存！")
                st.rerun()
