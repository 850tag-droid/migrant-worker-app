import json
from openai import OpenAI

def process_line_chat(api_key, text_content):
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    你是一位資深勞務專家與法律顧問。請分析以下 LINE 聊天紀錄，過濾垃圾訊息，提取出具備知識價值的「法令與實務」內容。
    
    請將內容整理成 JSON 列表格式，每個項目包含：
    1. category: 分類 (只能從中選擇：法規動態/行話解密/實務個案/勞檢應對)
    2. keywords: 核心關鍵字 (如：聘可、巴氏量表、洗工)
    3. subject: 社群口語/個案主題 (如：群友討論的限期離境爭議)
    4. legal_basis: 官方正式名稱/法規依據 (自動對照還原的正式法律條文)
    5. description: 完整說明與實務對策 (具體解決方案，支援長文字)

    聊天紀錄內容如下：
    ---
    {text_content}
    ---

    僅輸出 JSON 格式，不要有額外解釋。
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一個專業的勞務知識庫整理助手。"},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        result = json.loads(response.choices[0].message.content)
        # 假設返回格式是 {"data": [...]} 或直接是列表，這裡做個處理
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        elif isinstance(result, dict) and any(isinstance(v, list) for v in result.values()):
            # 找到第一個列表
            for v in result.values():
                if isinstance(v, list): return v
        return []
    except Exception as e:
        print(f"AI Processing Error: {e}")
        return []
