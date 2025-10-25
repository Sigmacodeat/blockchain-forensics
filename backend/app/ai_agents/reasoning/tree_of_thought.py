"""
Tree-of-Thought Reasoning Engine.
Generates multiple solution paths, evaluates each, selects best.
"""

import logging
import json
from typing import List, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ThoughtBranch(BaseModel):
    """Single branch in tree of thought"""
    branch_id: str
    plan: List[str]
    estimated_success: float  # 0-1
    estimated_cost: float  # execution time/resources
    pros: List[str]
    cons: List[str]
    selected: bool = False


class ToTResult(BaseModel):
    """Result of tree-of-thought reasoning"""
    query: str
    branches: List[ThoughtBranch]
    selected_branch: str
    execution_result: Any
    selection_reasoning: str


class TreeOfThoughtEngine:
    """
    Tree-of-Thought: Generate multiple investigation strategies.
    
    Example:
    Query: "Trace funds from mixer to destination"
    
    Branch 1: Direct forward trace
      - Pros: Simple, fast
      - Cons: Might lose trail in mixer
      - Success: 40%
      
    Branch 2: Backward trace from known destinations
      - Pros: Higher success rate
      - Cons: Slower
      - Success: 70%
      
    Branch 3: Combined + clustering
      - Pros: Highest success
      - Cons: Most expensive
      - Success: 85%
      
    Selected: Branch 3 (highest success)
    """
    
    def __init__(self):
        """Initialize ToT engine"""
        self.default_branches = 3
        logger.info("✅ TreeOfThoughtEngine initialized")
    
    async def reason(
        self,
        query: str,
        num_branches: int = 3
    ) -> ToTResult:
        """
        Generate and evaluate multiple investigation strategies.
        
        Args:
            query: User query
            num_branches: Number of strategies to generate
        
        Returns:
            ToTResult with all branches and selected path
        """
        try:
            # Import agent
            from app.ai_agents.agent import get_agent
            agent = get_agent()
            
            # Generate multiple plans
            plan_prompt = f"""
            Generate {num_branches} different investigation strategies for:
            
            Query: {query}
            
            For each strategy:
            1. Step-by-step approach
            2. Tools/techniques to use
            3. Estimated success probability (0-1)
            4. Pros and cons
            5. Estimated execution time (seconds)
            
            Respond with JSON array:
            [
                {{
                    "steps": ["step 1", "step 2", ...],
                    "success_probability": 0.0-1.0,
                    "execution_time": seconds,
                    "pros": ["pro 1", ...],
                    "cons": ["con 1", ...]
                }}
            ]
            """
            
            plans_result = await agent.llm.ainvoke([
                {"role": "system", "content": "You are an expert forensic investigator creating investigation strategies."},
                {"role": "user", "content": plan_prompt}
            ])
            
            # Parse plans
            try:
                plans_data = json.loads(plans_result.content)
            except json.JSONDecodeError:
                # Extract from markdown
                content = plans_result.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                plans_data = json.loads(content)
            
            # Create branches
            branches: List[ThoughtBranch] = []
            for idx, plan_data in enumerate(plans_data[:num_branches]):
                branches.append(ThoughtBranch(
                    branch_id=f"branch_{idx+1}",
                    plan=plan_data.get("steps", []),
                    estimated_success=plan_data.get("success_probability", 0.5),
                    estimated_cost=plan_data.get("execution_time", 1.0),
                    pros=plan_data.get("pros", []),
                    cons=plan_data.get("cons", [])
                ))
            
            # Select best branch
            if not branches:
                # Fallback: create simple plan
                branches.append(ThoughtBranch(
                    branch_id="fallback",
                    plan=["Execute standard investigation"],
                    estimated_success=0.6,
                    estimated_cost=1.0,
                    pros=["Simple approach"],
                    cons=["May miss details"]
                ))
            
            # Selection logic: prioritize success rate, then cost
            best_branch = max(branches, key=lambda b: (b.estimated_success, -b.estimated_cost))
            best_branch.selected = True
            
            # Generate selection reasoning
            selection_reasoning = f"""
            Selected {best_branch.branch_id} with {best_branch.estimated_success*100:.0f}% success rate.
            
            Reasoning:
            - Success probability: {best_branch.estimated_success}
            - Estimated time: {best_branch.estimated_cost}s
            - Pros: {', '.join(best_branch.pros)}
            """
            
            # Execute selected plan
            execution_result = await self._execute_plan(best_branch.plan, agent)
            
            return ToTResult(
                query=query,
                branches=branches,
                selected_branch=best_branch.branch_id,
                execution_result=execution_result,
                selection_reasoning=selection_reasoning
            )
            
        except Exception as e:
            logger.error(f"ToT reasoning error: {e}", exc_info=True)
            
            # Fallback
            fallback_branch = ThoughtBranch(
                branch_id="fallback",
                plan=["Error in planning"],
                estimated_success=0.0,
                estimated_cost=0.0,
                pros=[],
                cons=[str(e)]
            )
            
            return ToTResult(
                query=query,
                branches=[fallback_branch],
                selected_branch="fallback",
                execution_result={"error": str(e)},
                selection_reasoning=f"Error: {str(e)}"
            )
    
    async def _execute_plan(
        self,
        plan: List[str],
        agent: Any
    ) -> Dict[str, Any]:
        """
        Execute the selected plan step by step.
        
        Args:
            plan: List of steps to execute
            agent: ForensicAgent instance
        
        Returns:
            Execution results
        """
        results = []
        
        for step in plan:
            try:
                # Execute step via agent
                result = await agent.investigate(step)
                results.append({
                    "step": step,
                    "success": result.get("success", False),
                    "response": result.get("response", "")[:200]  # Truncate
                })
            except Exception as e:
                results.append({
                    "step": step,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "steps_completed": len(results),
            "steps_successful": sum(1 for r in results if r.get("success")),
            "results": results
        }


logger.info("✅ Tree-of-Thought Engine loaded")
