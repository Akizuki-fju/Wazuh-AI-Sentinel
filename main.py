import os
import requests
import urllib3
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# 1. 載入環境變數
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 設定：使用備用鑰匙 (已驗證成功) ---
WAZUH_API_URL = "https://192.168.56.103:55000"
WAZUH_USER = "*******"
WAZUH_PASS = r"***********"

# 2. 設定 LLM
llm = ChatOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
    model="meta/llama-3.1-70b-instruct",
    temperature=0.5,
)

# 3. 取得 Token
def get_wazuh_token():
    url = f"{WAZUH_API_URL}/security/user/authenticate"
    try:
        response = requests.post(url, auth=(WAZUH_USER, WAZUH_PASS), verify=False, timeout=10)
        if response.status_code == 200:
            return response.json()['data']['token']
        else:
            print(f"❌ 登入失敗: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 連線錯誤: {e}")
        return None

# 4. 定義工具 (改為查詢 Agent 狀態，保證路徑存在)
@tool
def check_wazuh_agents(query: str = ""):
    """
    查詢 Wazuh 連線的主機 (Agents) 狀態。
    可以用來確認有哪些電腦正在被監控，以及它們是否連線中。
    """
    token = get_wazuh_token()
    if not token:
        return "錯誤：無法取得 Token，請檢查帳號密碼。"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # --- 關鍵修改：改用 /agents 路徑 (這是絕對存在的) ---
    url = f"{WAZUH_API_URL}/agents?pretty=true"
    
    try:
        print(f"🔍 正在查詢 Wazuh Agents: {url} ...")
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            agents = data.get('data', {}).get('affected_items', [])
            
            if not agents:
                return "回報：目前沒有發現任何已註冊的 Agent。"
            
            result = f"✅ 成功連線！找到 {len(agents)} 台主機：\n"
            for agent in agents:
                status = agent.get('status', 'unknown')
                name = agent.get('name', 'unknown')
                ip = agent.get('ip', 'unknown')
                agent_id = agent.get('id', 'unknown')
                result += f"- [ID:{agent_id}] {name} ({ip}) - 狀態: {status}\n"
            
            return result
        else:
            return f"查詢失敗 (代碼 {response.status_code}): {response.text}"

    except Exception as e:
        return f"執行錯誤: {str(e)}"

# 5. 建立 Agent
tools = [check_wazuh_agents]
agent_executor = create_react_agent(llm, tools)

# 6. 執行
if __name__ == "__main__":
    print("=== Wazuh AI Hunter (最終驗證版) ===")
    # 自動幫妳問這個保證會贏的問題
    initial_question = "幫我檢查目前有哪些 Agent 連線中？" 
    print(f"妳 (預設): {initial_question}")
    
    try:
        response = agent_executor.invoke({"messages": [("user", initial_question)]})
        print(f"AI (Agent): {response['messages'][-1].content}")
    except Exception as e:
        print(f"❌ 錯誤: {e}")