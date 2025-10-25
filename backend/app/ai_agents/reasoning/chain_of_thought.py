"""
Chain-of-Thought Reasoning Engine.
Enables step-by-step reasoning for complex investigations.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)


class ThoughtStep(BaseModel):
    """Single step in chain of thought"""
    step_number: int
    thought: str
    reasoning: str
    confidence: float  # 0-1
    next_action: Optional[str] = None
    tool_called: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class CoTResult(BaseModel):
    """Result of chain-of-thought reasoning"""
    query: str
    thoughts: List[ThoughtStep]
    final_answer: str
    total_confidence: float
    execution_time_ms: float


class ChainOfThoughtEngine:
    """
    Enhanced Chain-of-Thought Reasoning.
    Agent thinks step-by-step like a human investigator.
    
    Example reasoning chain:
    1. "User asks about risk of address X"
       → Reasoning: "Need to gather data first"
       → Action: get_labels
       
    2. "Address has label 'mixer'"
       → Reasoning: "Mixers are high-risk"
       → Action: risk_score
       
    3. "Risk score is 0.85"
       → Reasoning: "High risk confirmed"
       → Final: "Yes, address is high-risk"
    """
    
    def __init__(self):
        """Initialize CoT engine"""
        self.max_steps = 10  # Prevent infinite loops
        logger.info("✅ ChainOfThoughtEngine initialized")
    
    async def reason(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> CoTResult:
        """
        Execute chain-of-thought reasoning.
        
        Args:
            query: User query to reason about
            context: Additional context (previous results, etc.)
        
        Returns:
            CoTResult with thoughts and final answer
        """
        start_time = datetime.utcnow()
        thoughts: List[ThoughtStep] = []
        
        try:
            # Import agent
            from app.ai_agents.agent import get_agent
            agent = get_agent()
            
            # Step 1: Initial analysis
            thoughts.append(ThoughtStep(
                step_number=1,
                thought=f"Analyzing query: {query}",
                reasoning="Breaking down the query to understand user intent",
                confidence=1.0,
                next_action="decompose_query"
            ))
            
            # Step 2: Decompose into sub-tasks
            decomposition_prompt = f"""
            Break down this forensic investigation query into logical steps.
            
            Query: {query}
            
            For each step:
            1. What needs to be done
            2. Which tool to use (if any)
            3. Why this step is necessary
            
            Respond with JSON array of steps:
            [
                {{
                    "action": "description",
                    "tool": "tool_name or null",
                    "reasoning": "why this is needed",
                    "confidence": 0.0-1.0
                }}
            ]
            """
            
            decomp_result = await agent.llm.ainvoke([
                {"role": "system", "content": "You are a forensic investigator planning an investigation."},
                {"role": "user", "content": decomposition_prompt}
            ])
            
            # Parse decomposition
            try:
                steps_data = json.loads(decomp_result.content)
            except json.JSONDecodeError:
                # Fallback: extract JSON from markdown code blocks
                content = decomp_result.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                steps_data = json.loads(content)
            
            # Execute each step
            step_num = 2
            for step_data in steps_data[:self.max_steps]:
                step_num += 1
                
                tool_name = step_data.get("tool")
                action = step_data.get("action", "")
                reasoning = step_data.get("reasoning", "")
                confidence = step_data.get("confidence", 0.7)
                
                thought = ThoughtStep(
                    step_number=step_num,
                    thought=action,
                    reasoning=reasoning,
                    confidence=confidence,
                    tool_called=tool_name
                )
                
                # Execute tool if specified
                if tool_name:
                    try:
                        from app.ai_agents.tools import ALL_TOOLS
                        
                        # Find tool
                        tool = next((t for t in ALL_TOOLS if t.name == tool_name), None)
                        
                        if tool:
                            # Extract params from query (simplified)
                            params = self._extract_params(query, tool_name)
                            result = await tool.ainvoke(params)
                            thought.result = result
                            
                            # Update reasoning with result
                            if isinstance(result, dict) and result.get("success"):
                                thought.reasoning += f" → Result: {json.dumps(result)[:200]}"
                    
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        thought.reasoning += f" → Error: {str(e)}"
                
                thoughts.append(thought)
            
            # Final synthesis
            synthesis_prompt = f"""
            Based on these investigation steps, provide a clear final answer.
            
            Query: {query}
            
            Steps taken:
            {json.dumps([t.dict() for t in thoughts], indent=2, default=str)}
            
            Provide a concise, evidence-based answer.
            """
            
            final_result = await agent.llm.ainvoke([
                {"role": "system", "content": "You are a forensic investigator providing conclusions."},
                {"role": "user", "content": synthesis_prompt}
            ])
            
            final_answer = final_result.content
            
            # Calculate total confidence
            total_confidence = sum(t.confidence for t in thoughts) / len(thoughts) if thoughts else 0.5
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return CoTResult(
                query=query,
                thoughts=thoughts,
                final_answer=final_answer,
                total_confidence=total_confidence,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"CoT reasoning error: {e}", exc_info=True)
            
            # Fallback: simple reasoning
            thoughts.append(ThoughtStep(
                step_number=1,
                thought="Error in reasoning chain",
                reasoning=str(e),
                confidence=0.0
            ))
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return CoTResult(
                query=query,
                thoughts=thoughts,
                final_answer=f"Unable to complete reasoning: {str(e)}",
                total_confidence=0.0,
                execution_time_ms=execution_time
            )
    
    def _extract_params(self, query: str, tool_name: str) -> Dict[str, Any]:
        """
        Extract parameters for tool from query.
        Simplified version - in production, use LLM for extraction.
        """
        params = {}
        
        # Extract address (0x... pattern)
        import re
        address_match = re.search(r'0x[a-fA-F0-9]{40}', query)
        if address_match:
            params["address"] = address_match.group(0)
        
        # Tool-specific params
        if "trace" in tool_name:
            params.setdefault("max_depth", 5)
            params.setdefault("direction", "forward")
        
        if "risk" in tool_name:
            params.setdefault("address", params.get("address", "0x0000"))
        
        return params


logger.info("✅ Chain-of-Thought Engine loaded")
