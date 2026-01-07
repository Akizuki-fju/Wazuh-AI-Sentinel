# 🛡️ Wazuh AI Security Ops Dashboard

> **An Intelligent SIEM Interface powered by Generative AI (Llama-3) & Wazuh API**
> 
> *結合生成式 AI 與資安監控，實現自動化威脅獵捕與戰情分析。*

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red?logo=streamlit)
![Wazuh](https://img.shields.io/badge/Security-Wazuh-blueviolet?logo=wazuh)
![AI](https://img.shields.io/badge/AI-NVIDIA%20NIM-green)

## 📖 專案簡介 (Introduction)

本專案是一個基於 **Wazuh SIEM** 的現代化資安戰情儀表板。透過整合 **NVIDIA NIM (Llama-3-70b)** 大型語言模型，將傳統繁雜的資安數據轉化為直觀的視覺化圖表與 AI 智能分析報告。

系統能夠即時監控 Agent 覆蓋率、自動擷取 MITRE ATT&CK 威脅警報，並由 AI 扮演資安長 (CISO) 角色，針對當前風險提供具體的修補建議。

## ✨ 核心功能 (Key Features)

* **📊 即時戰情儀表板 (Live Dashboard)**
    * 可視化呈現系統監控覆蓋率 (Coverage)。
    * 即時統計活躍主機 (Active) 與離線主機 (Disconnected) 數量。
* **🚨 威脅獵捕 (Threat Hunting)**
    * 自動對接 Wazuh API，擷取 MITRE ATT&CK 框架下的高風險警報。
    * 偵測異常程序與未授權的網路連接埠 (Ports)。
* **🤖 AI 資安智囊 (AI Security Analyst)**
    * 利用 LLM 自動分析 JSON 格式的原始日誌。
    * 生成全中文的風險評估報告與防禦建議。
* **🔒 企業級整合**
    * 支援 Wazuh Token 自動化認證管理。
    * 相容於自簽憑證 (Self-signed Cert) 的內部環境。

## 🛠️ 技術架構 (Tech Stack)

* **Frontend**: Streamlit (Python)
* **Backend**: Wazuh API (v4.x)
* **AI Engine**: LangChain + NVIDIA NIM (Llama-3.1-70b-instruct)
* **Environment**: Docker / VirtualBox (Ubuntu Server & Windows Agent)

## 🚀 快速開始 (Quick Start)

### 1. 安裝依賴 (Installation)

```bash
pip install streamlit requests python-dotenv langchain-openai langchain-community