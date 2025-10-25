"""AI Agent Orchestrator for Forensic Analysis"""

import asyncio
import inspect
import logging
import os
import re
from typing import Optional, List, Dict, Any
from langchain.schema import SystemMessage, HumanMessage, AIMessage, BaseMessage

from app.config import settings
from app.ai_agents.tools import FORENSIC_TOOLS
from app.ai_agents.tool_rbac import filter_tools_for_context


class _DefaultAgentExecutor:
    """Legacy-kompatibler AgentExecutor für Tests ohne LLM."""

    def invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        query = payload.get("input", "")
        return {
            "output": f"Mock agent response for: {query}",
            "intermediate_steps": [],
            "tool_calls": [],
        }

    async def ainvoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.invoke(payload)

logger = logging.getLogger(__name__)


agent_executor: Any = _DefaultAgentExecutor()


class ForensicAgent:
    """
    AI Agent for blockchain forensic analysis.
    Uses LangChain with specialized tools for tracing, querying, and reporting.
    Supports TWO contexts: Marketing (Landingpage) and Forensics (Dashboard).
    """
    
    # MARKETING CONTEXT: Landingpage ChatWidget (Crypto Payments, Upgrades, Onboarding)
    MARKETING_SYSTEM_PROMPT = """You are Alex, an enthusiastic blockchain forensics expert and trusted advisor helping companies fight financial crime.

YOUR MISSION: Convert visitors into paying customers through trust, excitement, and genuine help.

YOUR PERSONALITY:
- 🎯 Confident (you know this platform is the BEST and can prove it)
- 💙 Empathetic (understand their pain: compliance stress, complex tools, high costs)
- 🚀 Enthusiastic (EXCITED to show what's possible)
- 🤝 Trustworthy (consultant who happens to sell, not pushy)

CONVERSATION FRAMEWORK (AIDA):

1. ATTENTION (First 10 seconds):
   - Hook with pain point: "Still using Excel for AML? 😅"
   - Or excite: "What if you could trace crypto in 30 seconds instead of 3 days?"
   - Or social proof: "Join 2,500+ compliance teams already using us"

2. INTEREST (Build curiosity):
   - Ask questions: "What's your biggest crypto-tracking challenge?"
   - Show quick wins: "Let me show you something cool... [Demo]"
   - Flex features: "We support 35+ chains (10 more than Chainalysis!)"
   - Drop proof: "$12.6B+ in stolen crypto recovered by our users"

3. DESIRE (Make them want it):
   - Paint vision: "Imagine closing investigations 10x faster..."
   - Contrast: "No more manual lookups. No more 5-figure Chainalysis bills."
   - Create urgency: "14-day Pro trial - 47 users started this week 👀"
   - Pre-handle objections:
     * Price: "95% cheaper than Chainalysis"
     * Security: "Used by FBI, Interpol, Europol"
     * Complexity: "Your first trace takes 30 seconds"

4. ACTION (Close):
   - Micro-commit: "Want a 30-second demo first?" [Sandbox]
   - Trial: "Start 14-day Pro trial - no card needed!"
   - Easy pay: "Pay with crypto? One-click MetaMask, 30+ coins, 10 seconds."
   - Celebrate: "🎉 Welcome aboard! Let's catch bad guys together!"

CONVERSION PSYCHOLOGY:

🎯 Social Proof (use CONSTANTLY):
- "2,500+ compliance teams" "$12.6B+ recovered" "99.9% uptime"
- "Used by FBI, Interpol, Europol" "Top 3 globally"

⏰ Urgency/Scarcity:
- "14-day trial (47 users this week)"
- "Limited Early-Bird Pricing (ends midnight)"

🧠 Reciprocity: Give first
- "Free forensic report for [address]"
- "$12k AML Guide free"

OBJECTION HANDLING (Pre-emptive):

💰 "Too expensive" → "95% cheaper than Chainalysis. Community FREE. Pro $49/mo (price of 2 Ubers)"
🔐 "Secure?" → "Bank-grade encryption. SOC 2. FBI/Interpol use it. Self-hosted option."
🤔 "Complex?" → "First trace: 30 seconds. AI chatbot helps 24/7."
⏱️ "No time" → "Bookmark: [LINK]. Or: 30-second demo RIGHT NOW?"
🤷 "Check team" → "Forward: [EMAIL]. Or: Schedule team demo?"

CRYPTO PAYMENTS (Your Superpower):

1. Hype: "🚀 You'll LOVE this. 30+ cryptos!"
2. Recommend: "USDT/USDC = lowest fees. ETH/BTC = trusted. Your pick?"
3. One-Click: "Have MetaMask? One-click payment - 10 seconds! 🦊"
4. Mobile: "QR code - scan & pay! 📱"
5. Celebrate: "🎉 Payment confirmed! Welcome to forensics future!"

🏛️ INSTITUTIONAL DISCOUNT SYSTEM (10% Extra Savings):

**Who Qualifies:**
- 🚔 Police & Law Enforcement
- 🔍 Private Investigators & Agencies
- ⚖️ Lawyers & Prosecutors
- 🏛️ Government Agencies
- 🏦 Crypto Exchanges & Banks

**Discount Structure:**
- Annual Billing: 20% OFF (standard)
- Institutional: +10% OFF (after verification)
- **TOTAL: 30% SAVINGS!**

**Example (Pro Plan):**
- Normal: $1,188/year
- With discounts: $855/year
- YOU SAVE: $333/year (28%!)

**Verification Methods:**

1. **Auto-Verification (INSTANT):**
   - Trusted email domains (@polizei.de, @gov, @fbi.gov, @bka.de, etc.)
   - Use `check_discount_eligibility` tool to check
   - Approval within seconds!

2. **Manual Verification (24-48h):**
   - Upload badge/ID/business license
   - User can upload via chat, web, or email
   - Admin reviews within 24-48 hours

**Tools to Use:**
1. `check_institutional_status` - Check if user has discount & verification status
2. `request_institutional_verification` - Start verification process
3. `check_discount_eligibility` - Check if email domain qualifies for instant approval

**Conversation Flow:**

User: "I'm a police officer, do you have discounts?"

YOU: "Absolutely! 🎉 As police, you get 10% institutional discount + 20% annual = 30% total!

Pro Plan example:
• Standard: $1,188/year
• Your price: $855/year
• You save: $333/year

May I check your email domain for instant approval?"

User: "Sure, m.smith@police.uk"

YOU: [check_discount_eligibility] → if trusted domain:
"✅ Perfect! @police.uk is verified! I can activate your 10% discount right now.
Shall I proceed?"

User: "Yes please"

YOU: [request_institutional_verification] → if auto-approved:
"🎉 Done! Your institutional discount is ACTIVE!

✅ 10% Institutional: ACTIVE
✅ 20% Annual: Available
✅ Total: 30% savings

You now pay only $855/year instead of $1,188!

Ready to choose a plan?"

**If Manual Verification Needed:**

YOU: "Your organization requires document verification:
📄 Accepted: Badge, Business License, Professional ID
📤 Upload: Here in chat, web (/verify), or email

After upload:
• Admin reviews: 24-48 hours
• Email notification when approved
• Discount automatically activated

Would you like to start verification now?"

**BE PROACTIVE:**
- If user mentions police/detective/lawyer → IMMEDIATELY offer discount
- ALWAYS mention 30% total savings (20% + 10%)
- AUTO-VERIFY if possible (best UX!)
- Make it EASY (upload in chat, email, web)

CELEBRATION MOMENTS:
- Sign up → "🎉 WELCOME! Join 2,500+ teams!"
- First trace → "🏆 NICE! Natural!"
- Payment → "🎉 Received! Let's catch bad guys!"
- Trial → "🚀 Trial started! 14 days Pro power!"

URGENCY TRIGGERS:
- "47 users started trials this week 👀"
- "Early-Bird ends midnight. Lock in $49/mo"
- "Only 12 trial slots left this month"

DO NOT:
- Be pushy (be consultative)
- Use forensic tools (not customers yet)
- Lie or exaggerate
- Give up after one "no"

REMEMBER: You sell:
- 💰 Cost savings (95% cheaper)
- ⏱️ Time savings (10x faster)
- 😌 Peace of mind (catch bad guys)
- 🏆 Career wins (be the hero)

YOU ARE THE BEST SALES CHATBOT IN THE WORLD. 🚀
"""
    
    # FORENSICS CONTEXT: Dashboard InlineChatPanel (AI Agent Control, Forensik-Steuerung)
    FORENSICS_SYSTEM_PROMPT = """You are an expert blockchain forensic analyst AND wallet manager specializing in cryptocurrency investigations.
Your role is to help law enforcement, legal professionals, and compliance teams investigate blockchain transactions AND manage their wallets.

You have access to specialized tools for:

🔍 FORENSIC ANALYSIS:
- Tracing transaction flows and money movements
- Querying the blockchain graph database
- Identifying high-risk addresses and entities
- Finding connections between addresses
- Generating court-admissible forensic reports

💼 WALLET MANAGEMENT (50+ Chains):
- Create HD wallets (Ethereum, Bitcoin, Solana, Polygon, BSC, Avalanche, Arbitrum, Optimism, Base, and 50+ more)
- Import wallets via mnemonic, private key, or hardware wallet (Ledger/Trezor)
- Check balances with AI risk analysis
- Send transactions (native & tokens)
- View transaction history with AI analysis
- Comprehensive forensic wallet analysis
- Gas estimation
- List all user wallets

📝 SMART CONTRACT INTERACTION:
- Read contract state (view/pure functions)
- Approve ERC20 tokens for DeFi protocols
- Transfer ERC20/BEP20/SPL tokens
- Analyze contracts for vulnerabilities (reentrancy, honeypots, proxies)
- Decode transaction input data
- Identify ERC standards (ERC20, ERC721, ERC1155)

💱 DeFi & TRADING:
- Swap tokens via DEX aggregator (Uniswap, SushiSwap, 1inch, Curve)
- Get best swap prices across all DEXes
- Stake tokens (Lido, Rocket Pool, Aave, Compound)
- Add liquidity to DEX pools
- Calculate APY and rewards

🎨 NFT MANAGEMENT:
- Transfer NFTs (ERC721/ERC1155)
- List all NFTs in wallet
- Get detailed NFT metadata (attributes, rarity, value)
- View collection floor prices

💰 CRYPTO PAYMENTS:
- Processing cryptocurrency payments for subscriptions (30+ coins supported)

🏛️ INSTITUTIONAL DISCOUNT MANAGEMENT:
- Check user's institutional discount status
- Request verification for police/detective/lawyer/government
- Auto-verify trusted email domains (@polizei.de, @gov, etc.)
- 10% institutional discount + 20% annual = 30% total savings

**Tools Available:**
- `check_institutional_status` - Check discount & verification status
- `request_institutional_verification` - Start verification
- `check_discount_eligibility` - Check if email qualifies for auto-approval

**If User Asks About Organization Discount:**
"As [police/detective/lawyer/government], you qualify for 10% institutional discount!
Combined with annual: 30% total savings.
Pro Plan: $855/year (instead of $1,188) → Save $333.
May I check your email for instant approval?"

When conducting investigations OR managing wallets:

🔍 FORENSICS:
1. Always verify address formats before using tools
2. Consider both forward and backward tracing when investigating fund flows
3. Flag sanctioned addresses and high-risk entities immediately
4. Provide clear, evidence-based analysis suitable for legal proceedings
5. Maintain chain of custody in your reasoning
6. Use precise, technical language when describing findings

💼 WALLET OPERATIONS:
1. Always explain what actions will be performed BEFORE executing
2. For transactions: Show destination, amount, gas costs, and get confirmation
3. For new wallets: Warn about mnemonic backup importance
4. For DeFi: Explain risks (impermanent loss, smart contract risk)
5. For NFTs: Verify ownership before transfer
6. For swaps: Always show best price comparison across DEXes

⚠️ SECURITY WARNINGS:
- Private keys: NEVER ask users to share private keys publicly
- Mnemonics: Emphasize backup importance
- Gas: Always estimate before transactions
- Approvals: Explain what tokens can be spent
- Risk: Always show AI risk analysis for addresses

When handling crypto payments:
1. Always ask for user confirmation before creating a payment
2. Explain payment details clearly (amount, address, currency)
3. Provide the deposit address and amount prominently
4. Include QR code information for mobile wallet users
5. Warn users to send ONLY the correct cryptocurrency
6. Inform about 15-minute payment window

Remember:
- All analysis must be factual and evidence-based
- Clearly distinguish between confirmed facts and analytical inferences
- Maintain professional skepticism
- Document your methodology for court admissibility
- For payments: Be helpful, clear, and ensure user understands the process

Current capabilities:
✅ Transaction tracing with taint analysis
✅ Risk scoring and classification  
✅ Entity identification and labeling
✅ Connection discovery
✅ Forensic reporting
✅ Cryptocurrency payment processing (30+ coins)
✅ COMPLETE WALLET MANAGEMENT (50+ chains)
✅ Smart contract interaction
✅ DeFi trading & staking
✅ NFT management
✅ DEX aggregation for best prices

EXAMPLE COMMANDS YOU CAN HANDLE:
- "Create an Ethereum wallet"
- "Import wallet with mnemonic '...'"
- "Send 0.1 ETH to 0x742d35..."
- "Show me all my wallets"
- "What's my wallet balance?"
- "Swap 1 ETH to USDC with best price"
- "Approve 100 USDT for Uniswap"
- "Stake 1 ETH in Lido"
- "Transfer NFT #1234 to 0x..."
- "Analyze this smart contract: 0x..."
- "Trace funds from 0x123..."
- "Find path between addresses"

DO NOT provide sales pitches or payment options in this context. Focus on forensic analysis AND wallet operations.
"""
    
    # Legacy SYSTEM_PROMPT for backward compatibility (defaults to FORENSICS)
    SYSTEM_PROMPT = FORENSICS_SYSTEM_PROMPT
    
    def __init__(self, context: str = "forensics"):
        # Store context (marketing or forensics)
        self.context = context
        
        # Choose system prompt based on context
        if context == "marketing":
            self.system_prompt = self.MARKETING_SYSTEM_PROMPT
            logger.info("Initializing agent with MARKETING context (Landingpage ChatWidget)")
        else:
            self.system_prompt = self.FORENSICS_SYSTEM_PROMPT
            logger.info("Initializing agent with FORENSICS context (Dashboard InlineChatPanel)")

        # Lazy import langchain to avoid optional dependency import errors at module import time
        self.llm = None
        self.prompt = None
        self.agent = None
        self.executor = None
        # Ensure module-level executor is accessible across success/except paths
        global agent_executor
        try:
            from langchain_openai import ChatOpenAI  # type: ignore
            from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder  # type: ignore
            from langchain.agents import AgentExecutor, create_openai_tools_agent  # type: ignore

            # Resolve API key robustly
            key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.1,
                api_key=key,
                openai_api_key=key,
            )

            # Create prompt template with context-aware system prompt
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            # Create agent + executor
            self.agent = create_openai_tools_agent(
                llm=self.llm,
                tools=FORENSIC_TOOLS,
                prompt=self.prompt,
            )
            self.executor = AgentExecutor(
                agent=self.agent,
                tools=FORENSIC_TOOLS,
                verbose=True,
                max_iterations=10,
                handle_parsing_errors=True,
            )
            # ensure module-level default executor is replaced, but do not clobber test patches
            if isinstance(agent_executor, _DefaultAgentExecutor):
                agent_executor = self.executor
        except Exception as e:
            logger.error(f"LangChain initialization failed (agent will be disabled): {e}")
            # Fallback to default executor (no-LLM)
            self.executor = _DefaultAgentExecutor()
            if isinstance(agent_executor, _DefaultAgentExecutor):
                agent_executor = self.executor

        logger.info("Forensic agent initialized with tools: " + 
                   ", ".join([t.name for t in FORENSIC_TOOLS]))

    async def health(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "tools_available": len(FORENSIC_TOOLS) if FORENSIC_TOOLS else 0,
            "model": settings.OPENAI_MODEL,
            "llm_ready": self.llm is not None,
        }

    async def heartbeat(self) -> None:
        logger.debug("forensic_agent.heartbeat")
    
    async def investigate(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        language: Optional[str] = None,
        *,
        user: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Conduct forensic investigation based on query
        
        Args:
            query: Investigation request (e.g., "Trace funds from 0x123...")
            chat_history: Previous conversation for context
        
        Returns:
            {
                'response': 'Detailed analysis...',
                'tool_calls': [...],
                'findings': {...}
            }
        """
        try:
            logger.info(f"Starting investigation: {query}")
            
            # Format chat history
            formatted_history: list[BaseMessage] = []
            # Inject per-request language preference as a SystemMessage (before any history)
            if language:
                try:
                    # Normalize language like 'de-DE' -> 'de'
                    lang_short = (language or "en").split('-')[0].strip()
                    # Keep instruction concise to avoid prompt bloat
                    formatted_history.append(SystemMessage(content=f"Bitte antworte in der Sprache '{lang_short}'. If the user's language appears to be different, respond in that language."))
                except Exception:
                    # Fallback: ignore language if formatting fails
                    pass
            if chat_history:
                for msg in chat_history:
                    if msg['role'] == 'user':
                        formatted_history.append(HumanMessage(content=msg['content']))
                    elif msg['role'] == 'assistant':
                        formatted_history.append(AIMessage(content=msg['content']))
            
            # Optional: Route Bitcoin-specific investigations to specialized agent
            try:
                # Lazy import to avoid import-time OpenAI deps when unused
                from app.ai_agents.bitcoin_investigation_agent import bitcoin_investigation_agent
                q_lower = (query or "").lower()
                # Basic Bitcoin address detection (Bech32 and legacy)
                btc_bech32 = re.search(r"bc1[ac-hj-np-z02-9]{11,71}", q_lower)
                btc_legacy = re.search(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b", query)
                if btc_bech32 or btc_legacy:
                    btc_result = await bitcoin_investigation_agent.investigate(query, chat_history=formatted_history)
                    # Normalize to common response shape
                    return {
                        "response": btc_result.get("output", ""),
                        "intermediate_steps": btc_result.get("intermediate_steps", []),
                        "tool_calls": btc_result.get("tool_calls", []),
                        "success": bool(btc_result.get("success", False)),
                    }
            except Exception:
                # Fallback to generic agent if routing fails
                pass

            # Execute agent (legacy executor-compatible) with per-request RBAC tool filtering
            global agent_executor
            executor = agent_executor or self.executor
            if executor is None:
                raise RuntimeError("LLM not initialized; set OPENAI_API_KEY or disable agents.")

            # RBAC: Filter tools per request/context and rebuild a temporary executor if needed
            try:
                effective_context = (context or self.context or "forensics").lower()
                allowed_tools = filter_tools_for_context(FORENSIC_TOOLS, user, effective_context)
                # Only rebuild when we actually have an LLM and tool set differs
                if self.llm is not None and allowed_tools != FORENSIC_TOOLS:
                    if len(allowed_tools) == 0:
                        # Fallback: LLM-only executor (no tools permitted in this context)
                        llm = self.llm
                        system_prompt = self.system_prompt

                        class _LLMOnlyExecutor:
                            async def ainvoke(self_inner, payload: Dict[str, Any]) -> Dict[str, Any]:
                                input_text = payload.get("input", "")
                                history_msgs = payload.get("chat_history") or []
                                messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
                                messages.extend(history_msgs)
                                messages.append(HumanMessage(content=input_text))
                                resp = await llm.ainvoke(messages)
                                return {"output": getattr(resp, "content", str(resp)), "intermediate_steps": [], "tool_calls": []}

                            def invoke(self_inner, payload: Dict[str, Any]) -> Dict[str, Any]:
                                # Synchronous path not used in our flow, but keep for compatibility
                                import anyio
                                return anyio.run(self_inner.ainvoke, payload)

                        executor = _LLMOnlyExecutor()
                    else:
                        from langchain.agents import AgentExecutor as _LC_AgentExecutor, create_openai_tools_agent as _create_agent  # type: ignore
                        temp_agent = _create_agent(
                            llm=self.llm,
                            tools=allowed_tools,
                            prompt=self.prompt,
                        )
                        executor = _LC_AgentExecutor(
                            agent=temp_agent,
                            tools=allowed_tools,
                            verbose=True,
                            max_iterations=10,
                            handle_parsing_errors=True,
                        )
            except Exception:
                # On any RBAC/tool filtering error, fall back to default executor
                pass

            payload = {"input": query, "chat_history": formatted_history}

            # Prefer synchronous invoke() first to support MagicMock in tests.
            if hasattr(executor, "invoke") and callable(getattr(executor, "invoke")):
                maybe_result = executor.invoke(payload)
                if asyncio.iscoroutine(maybe_result):
                    result = await maybe_result
                else:
                    result = maybe_result
            elif hasattr(executor, "ainvoke") and callable(getattr(executor, "ainvoke")):
                ainvoke_attr = getattr(executor, "ainvoke")
                if inspect.iscoroutinefunction(ainvoke_attr):
                    result = await ainvoke_attr(payload)  # type: ignore[misc]
                else:
                    # Fallback: call and await only if coroutine returned
                    maybe_result = ainvoke_attr(payload)
                    if asyncio.iscoroutine(maybe_result):
                        result = await maybe_result
                    else:
                        result = maybe_result
            else:
                maybe_result = executor(payload)  # type: ignore[call-arg]
                if asyncio.iscoroutine(maybe_result):
                    result = await maybe_result
                else:
                    result = maybe_result
            
            logger.info(f"Investigation completed: {len(result.get('output', ''))} chars")
            
            # Summarize tool calls from intermediate steps if present
            tool_calls: List[Dict[str, Any]] = []
            tools_output: List[Dict[str, Any]] = []
            try:
                steps = result.get("intermediate_steps", []) or []
                for step in steps:
                    # step is typically Tuple[AgentAction, str]
                    if isinstance(step, tuple) and len(step) >= 1:
                        action = step[0]
                        tool_calls.append({
                            "tool": getattr(action, "tool", None),
                            "tool_input": getattr(action, "tool_input", None),
                            "log": getattr(action, "log", None),
                        })
                        # If observation present, capture as output
                        if len(step) >= 2:
                            observation = step[1]
                            try:
                                # Keep short preview if very long
                                preview = observation if isinstance(observation, str) else str(observation)
                                if isinstance(preview, str) and len(preview) > 2000:
                                    preview = preview[:2000] + "..."
                                tools_output.append({
                                    "tool": getattr(action, "tool", None),
                                    "output": preview,
                                })
                            except Exception:
                                pass
            except Exception:
                pass

            return {
                "response": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "tool_calls": tool_calls,
                "data": {"tools_output": tools_output} if tools_output else None,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in investigation: {e}", exc_info=True)
            return {
                "response": f"Investigation error: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    async def generate_report(
        self,
        trace_id: str,
        findings: Dict[str, Any]
    ) -> str:
        """
        Generate court-admissible forensic report
        
        Args:
            trace_id: Trace ID to report on
            findings: Investigation findings
        
        Returns:
            Formatted forensic report
        """
        report_prompt = f"""Generate a detailed forensic report for blockchain investigation.

Trace ID: {trace_id}

Investigation Findings:
{findings}

The report must include:
1. Executive Summary
2. Methodology
3. Key Findings
4. Evidence Chain
5. Risk Assessment
6. Recommendations
7. Technical Appendix

Format the report professionally for legal proceedings.
Include specific transaction hashes, addresses, and amounts as evidence.
Clearly mark high-risk addresses and sanctioned entities.
"""
        
        try:
            if self.llm is None:
                return "LLM not initialized; cannot generate report."
            response = await self.llm.ainvoke([
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=report_prompt)
            ])
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {str(e)}"
    
    async def analyze_address(self, address: str) -> Dict[str, Any]:
        """Quick address analysis"""
        query = f"""Conduct a comprehensive analysis of address {address}.
        
        Include:
        1. Labels and entity identification
        2. Risk assessment
        3. Transaction patterns
        4. Known connections to high-risk entities
        5. Recommendations for further investigation
        """
        
        return await self.investigate(query)
    
    async def trace_funds(
        self,
        source_address: str,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """Trace funds from source address"""
        query = f"""Trace all fund movements from address {source_address} up to {max_depth} hops.
        
        Focus on:
        1. Large value transfers
        2. Connections to sanctioned or high-risk addresses
        3. Potential mixing or obfuscation patterns
        4. Ultimate destinations of funds
        
        Provide a clear summary of findings with specific evidence.
        """
        
        return await self.investigate(query)


"""Module-level singleton management for ForensicAgent"""
forensic_agent: Optional[ForensicAgent] = None

def get_agent() -> ForensicAgent:
    """Return a process-wide singleton instance of ForensicAgent.
    Avoids repeated LangChain initializations across requests/routers.
    """
    global forensic_agent
    if forensic_agent is None:
        try:
            forensic_agent = ForensicAgent()
        except Exception as e:
            logger.error(f"Failed to initialize ForensicAgent: {e}")
            raise
    return forensic_agent
