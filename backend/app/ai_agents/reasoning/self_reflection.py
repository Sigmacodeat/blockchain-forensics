"""
Self-Reflection Engine.
Agent evaluates its own answers for quality and correctness.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ReflectionResult(BaseModel):
    """Result of self-reflection"""
    original_answer: str
    quality_score: float  # 0-1
    issues_found: List[str]
    improvements: List[str]
    revised_answer: Optional[str] = None
    should_retry: bool


class SelfReflectionEngine:
    """
    Self-Reflection: Agent evaluates own answers.
    
    Quality checks:
    - Is the answer correct?
    - Is evidence provided?
    - Are there logical flaws?
    - What's missing?
    
    If quality < threshold → Generate improved answer
    """
    
    def __init__(self, quality_threshold: float = 0.7):
        """
        Initialize reflection engine.
        
        Args:
            quality_threshold: Minimum quality to accept (0-1)
        """
        self.quality_threshold = quality_threshold
        logger.info(f"✅ SelfReflectionEngine initialized (threshold: {quality_threshold})")
    
    async def reflect(
        self,
        query: str,
        answer: str,
        evidence: Optional[Dict] = None
    ) -> ReflectionResult:
        """
        Reflect on answer quality.
        
        Args:
            query: Original user query
            answer: Agent's answer
            evidence: Supporting evidence (tool results, etc.)
        
        Returns:
            ReflectionResult with quality assessment and improvements
        """
        try:
            # Import agent
            from app.ai_agents.agent import get_agent
            agent = get_agent()
            
            # Reflection prompt
            reflection_prompt = f"""
            As a quality control expert, evaluate this forensic analysis.
            
            Query: {query}
            Answer: {answer}
            Evidence: {json.dumps(evidence or {}, default=str)[:500]}
            
            Assess:
            1. Is the answer correct? (yes/no/uncertain)
            2. Completeness (0-10 scale)
            3. Is evidence provided? (yes/no)
            4. Logical flaws (list them)
            5. What's missing? (list gaps)
            6. Quality score (0-1)
            7. Should revise? (yes/no)
            
            Respond with JSON:
            {{
                "correct": "yes/no/uncertain",
                "completeness": 0-10,
                "has_evidence": true/false,
                "flaws": ["flaw 1", ...],
                "missing": ["gap 1", ...],
                "quality_score": 0.0-1.0,
                "should_revise": true/false
            }}
            """
            
            reflection_result = await agent.llm.ainvoke([
                {"role": "system", "content": "You are a forensic analysis quality control expert."},
                {"role": "user", "content": reflection_prompt}
            ])
            
            # Parse reflection
            try:
                reflection_data = json.loads(reflection_result.content)
            except json.JSONDecodeError:
                # Extract from markdown
                content = reflection_result.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                reflection_data = json.loads(content)
            
            # Extract assessment
            quality_score = reflection_data.get("quality_score", 0.5)
            issues = reflection_data.get("flaws", [])
            missing = reflection_data.get("missing", [])
            should_revise = reflection_data.get("should_revise", False) or quality_score < self.quality_threshold
            
            # Generate improved answer if needed
            revised_answer = None
            if should_revise:
                revision_prompt = f"""
                The previous answer needs improvement.
                
                Query: {query}
                Previous Answer: {answer}
                Issues: {', '.join(issues)}
                Missing: {', '.join(missing)}
                Evidence: {json.dumps(evidence or {}, default=str)[:500]}
                
                Provide a complete, evidence-based answer that addresses all issues.
                """
                
                revised_result = await agent.llm.ainvoke([
                    {"role": "system", "content": "You are a forensic investigator providing detailed analysis."},
                    {"role": "user", "content": revision_prompt}
                ])
                
                revised_answer = revised_result.content
            
            return ReflectionResult(
                original_answer=answer,
                quality_score=quality_score,
                issues_found=issues,
                improvements=missing,
                revised_answer=revised_answer,
                should_retry=should_revise
            )
            
        except Exception as e:
            logger.error(f"Reflection error: {e}", exc_info=True)
            
            # Fallback: assume answer is okay
            return ReflectionResult(
                original_answer=answer,
                quality_score=0.5,
                issues_found=[f"Reflection error: {str(e)}"],
                improvements=[],
                revised_answer=None,
                should_retry=False
            )
    
    async def multi_pass_reflection(
        self,
        query: str,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Multi-pass reflection: Iterate until quality acceptable.
        
        Args:
            query: User query
            max_iterations: Maximum reflection passes
        
        Returns:
            Best answer after reflections
        """
        # Import agent
        from app.ai_agents.agent import get_agent
        agent = get_agent()
        
        # Initial answer
        result = await agent.investigate(query)
        current_answer = result.get("response", "")
        evidence = result.get("tool_calls", {})
        
        iteration = 0
        best_score = 0.0
        best_answer = current_answer
        
        while iteration < max_iterations:
            iteration += 1
            
            # Reflect
            reflection = await self.reflect(query, current_answer, evidence)
            
            logger.info(f"Reflection {iteration}: Quality={reflection.quality_score:.2f}")
            
            # Update best if better
            if reflection.quality_score > best_score:
                best_score = reflection.quality_score
                best_answer = current_answer
            
            # Stop if quality acceptable
            if reflection.quality_score >= self.quality_threshold:
                logger.info(f"Quality threshold reached: {reflection.quality_score:.2f}")
                break
            
            # Try to improve
            if reflection.revised_answer:
                current_answer = reflection.revised_answer
            else:
                break  # Can't improve further
        
        return {
            "query": query,
            "answer": best_answer,
            "quality_score": best_score,
            "iterations": iteration,
            "success": True
        }


logger.info("✅ Self-Reflection Engine loaded")
