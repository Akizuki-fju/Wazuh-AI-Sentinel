import streamlit as st
import os
import requests
import urllib3
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# --- 1. 基礎設定 ---
st.set_page_config(page_title="Wazuh AI SIEM Dashboard", page_icon="🛡️", layout="wide")
st.title("🛡️ Wazuh AI SIEM Dashboard (完整版)")
st.markdown("### 整合功能：即時監控覆蓋率 | 風險警報分析 | 資安建議報告")

load_dotenv()
# [安全認證功能]：忽略自簽憑證 (Self-signed Cert) 的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 2. API 連線與認證機制 ---
WAZUH_API_URL = "https://192.168.56.103:55000"
WAZUH_USER = "wazuh-wui"
WAZUH_PASS = r"DSFRV4u?ztWElnh2Mt0i?qU?9hOn3Fsq"

def get_token():
    """
    [安全認證功能]
    實作自動化 Token 獲取。
    支援自簽憑證環境 (verify=False)。
    """
    try:
        resp = requests.post(f"{WAZUH_API_URL}/security/user/authenticate", 
                           auth=(WAZUH_USER, WAZUH_PASS), verify=False, timeout=5)
        if resp.status_code == 200: return resp.json()['data']['token']
    except: pass
    return None

def api_get(endpoint):
    """通用 API 請求函式 (自動帶入 Token)"""
    token = get_token()
    if not token: return None
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{WAZUH_API_URL}{endpoint}", headers=headers, verify=False, timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except: return None

# --- 3. 資料獲取工具 (Dashboard + Alerts) ---

def get_agent_details(agent_id):
    """取得單一 Agent 的細節 (Process/Port)"""
    proc_data = api_get(f"/syscollector/{agent_id}/processes?limit=5&sort=-memory")
    processes = [f"{p.get('name')} (PID:{p.get('pid')})" for p in proc_data['data']['affected_items']] if proc_data and 'affected_items' in proc_data.get('data', {}) else []

    port_data = api_get(f"/syscollector/{agent_id}/ports?limit=5")
    ports = [f"{p.get('protocol')}/{p.get('local',{}).get('port')}" for p in port_data['data']['affected_items']] if port_data and 'affected_items' in port_data.get('data', {}) else []

    return {"processes": processes, "ports": ports}

def get_threat_alerts():
    """
    [警報分析功能]
    自動擷取最新的資安警報 (改用 MITRE 統計，確保有資料)。
    """
    data = api_get("/mitre/attacks?limit=5")
    alerts = []
    if data and 'affected_items' in data.get('data', {}):
        for item in data['data']['affected_items']:
            alerts.append({
                "tactic": item.get('phase_name', 'Unknown'),
                "count": item.get('count', 0),
                "severity": "High" # MITRE 事件通常視為高風險
            })
    return alerts

def run_full_analysis():
    """
    [全域資料彙整]
    同時包含：覆蓋率狀態 + 威脅警報
    """
    # 1. 取得 Agent 狀態
    agent_data = api_get("/agents?pretty=true")
    if not agent_data or 'affected_items' not in agent_data.get('data', {}):
        return None

    all_agents = agent_data['data']['affected_items']
    
    # 初始化 Dashboard 結構
    dashboard_data = {
        "system_health": {
            "total_agents": len(all_agents),
            "active_agents": 0,
            "coverage_percent": "0%"
        },
        "recent_threats": [], # 這裡存放警報資料
        "active_hosts": [],
        "offline_hosts": []
    }

    # 2. 填充警報資料
    dashboard_data["recent_threats"] = get_threat_alerts()

    # 3. 填充主機資料
    for agent in all_agents:
        info = {"id": agent['id'], "name": agent['name'], "ip": agent['ip'], "status": agent['status']}
        
        if agent['status'] == 'active':
            dashboard_data["system_health"]["active_agents"] += 1
            info.update(get_agent_details(agent['id']))
            dashboard_data["active_hosts"].append(info)
        else:
            dashboard_data["offline_hosts"].append(info)

    # 計算覆蓋率
    if dashboard_data["system_health"]["total_agents"] > 0:
        cov = (dashboard_data["system_health"]["active_agents"] / dashboard_data["system_health"]["total_agents"]) * 100
        dashboard_data["system_health"]["coverage_percent"] = f"{cov:.1f}%"

    return dashboard_data

# --- 4. 初始化 AI ---
if "llm" not in st.session_state:
    st.session_state.llm = ChatOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv("NVIDIA_API_KEY"),
        model="meta/llama-3.1-70b-instruct",
        temperature=0.3,
    )

# --- 5. 介面邏輯 ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "SIEM 系統就緒。具備「警報分析」與「覆蓋率監控」功能。請輸入「啟動全域分析」。"}]

for msg in st.session_state.messages:
    if msg["role"] != "dashboard_snapshot":
        st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("請輸入指令..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    is_scan = any(k in prompt.lower() for k in ["全域", "分析", "監控", "scan", "dashboard"])

    with st.chat_message("assistant"):
        if is_scan:
            with st.spinner("正在執行：身份驗證 -> 警報擷取 -> 覆蓋率計算..."):
                data = run_full_analysis()
                
                if data:
                    # --- UI 區塊 1: 系統狀態 ---
                    st.markdown("### 📊 系統狀態 (System Status)")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("監控覆蓋率", data["system_health"]["coverage_percent"])
                    c2.metric("活躍主機", data["system_health"]["active_agents"])
                    c3.metric("偵測到的威脅戰術", len(data["recent_threats"]), delta_color="inverse")

                    # --- UI 區塊 2: 警報摘要 (Alerts) ---
                    if data["recent_threats"]:
                        st.warning(f"🚨 發現 {len(data['recent_threats'])} 類活躍威脅戰術 (MITRE ATT&CK)！")
                        st.dataframe(data["recent_threats"])
                    else:
                        st.success("✅ 目前無顯著威脅警報。")

                    # --- UI 區塊 3: 原始資料 ---
                    with st.expander("🛠️ 查看完整 SIEM 數據 (JSON)"):
                        st.json(data)

                    # --- UI 區塊 4: AI 綜合報告 ---
                    final_prompt = f"""
                    User Request: {prompt}
                    SIEM Data (JSON):
                    {json.dumps(data, ensure_ascii=False)}
                    
                    Task: Act as a CISO (Chief Information Security Officer). 
                    Write a comprehensive report.
                    1. **Risk Assessment**: Analyze the 'recent_threats' section. Is the system under attack?
                    2. **Coverage Analysis**: Discuss active vs offline agents.
                    3. **Conclusion**: Is the security posture healthy?
                    
                    Language: Traditional Chinese (繁體中文).
                    """
                    response_content = st.session_state.llm.invoke([HumanMessage(content=final_prompt)]).content
                    st.markdown("### 📝 AI 風險評估報告")
                    st.write(response_content)
                    
                    st.session_state.messages.append({"role": "assistant", "content": response_content})
                else:
                    st.error("無法取得數據，請檢查 Token 認證或 Wazuh 連線。")
        else:
            response_content = st.session_state.llm.invoke([HumanMessage(content=prompt)]).content
            st.write(response_content)
            st.session_state.messages.append({"role": "assistant", "content": response_content})