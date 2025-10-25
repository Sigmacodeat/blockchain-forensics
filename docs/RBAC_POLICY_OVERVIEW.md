# RBAC Policy Übersicht
## Tool-basierte Access Control für AI-Agents

### SAFE_TOOLS (Marketing-Kontext)
Erlaubte Tools im Marketing-Context (unabhängig von Plan/Rollen):
- `text_extract`, `code_extract`, `intelligence_stats`, `intelligence_list_flags`
- `list_alert_rules`, `get_user_plan`, `get_available_cryptocurrencies`
- `get_payment_estimate`, `recommend_best_currency`, `suggest_web3_payment`
- `create_crypto_payment`, `retry_failed_payment`, `check_payment_status`
- `get_payment_history`

### TOOL_POLICIES (Forensik-Kontext)
Sensible Forensik-Tools mit Plan/Rollen-Gates:

#### Community-Plan Tools
- `get_labels`, `bridge_lookup` (Community+)
- `submit_community_report` (Community+)

#### Starter-Plan Tools
- `trace_address`, `risk_score`, `threat_intel_enrich` (Starter+, analyst/admin)

#### Pro-Plan Tools
- `query_graph`, `find_path`, `cluster_analysis`, `cross_chain_analysis` (Pro+, analyst/admin)
- `create_wallet`, `get_wallet_balance`, `monitor_wallet` (Pro+, admin/analyst)
- `read_contract_state`, `verify_contract_source`, `get_contract_events` (Pro+, analyst/admin)
- `get_lp_positions`, `get_nft_metadata` (Pro+, analyst/admin)
- `get_firewall_stats` (Pro+, analyst/admin)

#### Business-Plan Tools
- `trigger_alert` (Business+, admin)
- `run_playbooks` (Business+, admin)
- `write_evidence` (Business+, admin/analyst)
- `send_transaction`, `sign_message`, `export_wallet_data` (Business+, admin)
- `deploy_contract`, `write_contract` (Business+, admin)
- `revoke_token_approval` (Business+, admin)
- `swap_tokens`, `add_liquidity`, `remove_liquidity`, `mint_nft`, `transfer_nft` (Business+, admin)
- `get_institution_details`, `onboard_institution` (Business+, admin/analyst)

#### Plus-Plan Tools
- `advanced_trace` (Plus+, analyst/admin)
- `scan_transaction_firewall`, `scan_token_approval`, `scan_url_phishing` (Plus+, analyst/admin)

#### Enterprise-Plan Tools
- `verify_institution` (Enterprise+, admin/analyst)
- `add_to_firewall_whitelist`, `add_to_firewall_blacklist` (Enterprise+, admin)

### RBAC-Architektur
- **Marketing**: Nur SAFE_TOOLS erlaubt (kein Plan-Gate)
- **Forensik**: Default-Allow für ungelistete Tools, explizite Policies für sensible
- **Fallback**: Bei fehlendem Tool-Access → LLM-only Executor (keine Tools, aber Antwort)
- **Feature-Flag**: `ENABLE_AGENT_TOOL_RBAC=false` für Legacy-Verhalten

### Implementation
- `backend/app/ai_agents/tool_rbac.py`: Policies & Filter-Funktionen
- `backend/app/ai_agents/agent.py`: Tool-Filtering pro Request
- Tests: `backend/tests/test_tool_rbac.py`
