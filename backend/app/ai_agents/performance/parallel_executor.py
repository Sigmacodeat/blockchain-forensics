"""
Parallel Tool Execution Engine.
Executes independent AI agent tools in parallel for maximum performance.
"""

import logging
import asyncio
from typing import List, Dict, Any, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class ParallelToolExecutor:
    """
    Executes independent AI agent tools in parallel.
    
    Example:
        Sequential:  risk_score → get_labels → query_graph (1500ms)
        Parallel:    [risk_score, get_labels, query_graph] (500ms)
    
    Performance Goals:
    - Parallel speedup: 2-3x for independent tools
    - No deadlocks or race conditions
    - Graceful error handling per tool
    """
    
    def __init__(self):
        """Initialize parallel executor"""
        # Dependency graph for tools
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # Register known dependencies
        self._register_dependencies()
        
        logger.info("✅ ParallelToolExecutor initialized")
    
    def _register_dependencies(self) -> None:
        """
        Register known tool dependencies.
        
        Dependencies mean: Tool B needs output from Tool A.
        These must be executed sequentially.
        """
        # trace_address must run before tools using its results
        self.dependencies["risk_score"].add("trace_address")
        self.dependencies["get_labels"].add("trace_address")
        self.dependencies["find_path"].add("trace_address")
        
        # Advanced trace must run before cluster analysis
        self.dependencies["cluster_analysis"].add("advanced_trace")
        
        # Query graph can depend on trace results
        self.dependencies["query_graph"].add("trace_address")
        
        logger.debug(f"Registered {len(self.dependencies)} tool dependencies")
    
    def _analyze_dependencies(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Analyze tool dependencies and group into execution stages.
        
        Args:
            tool_calls: List of tool call dictionaries with 'tool' and 'params'
        
        Returns:
            List of groups, where each group can be executed in parallel
        
        Example:
            Input: [trace, risk_score, get_labels, query_graph]
            Output: [[trace], [risk_score, get_labels, query_graph]]
                    └─ Stage 1    └─ Stage 2 (parallel)
        """
        # Extract tool names
        tool_names = [tc.get("tool", "") for tc in tool_calls]
        
        # Build execution stages
        stages: List[List[Dict[str, Any]]] = []
        executed: Set[str] = set()
        remaining = tool_calls.copy()
        
        max_iterations = len(tool_calls) + 1  # Prevent infinite loops
        iteration = 0
        
        while remaining and iteration < max_iterations:
            iteration += 1
            current_stage: List[Dict[str, Any]] = []
            
            # Find tools that can execute now (dependencies satisfied)
            for tool_call in remaining[:]:
                tool_name = tool_call.get("tool", "")
                
                # Check if dependencies are satisfied
                deps = self.dependencies.get(tool_name, set())
                if deps.issubset(executed):
                    # All dependencies met
                    current_stage.append(tool_call)
                    remaining.remove(tool_call)
                    executed.add(tool_name)
            
            if current_stage:
                stages.append(current_stage)
            else:
                # No progress - add remaining as final stage (break cycle)
                if remaining:
                    stages.append(remaining)
                break
        
        logger.debug(f"Grouped {len(tool_calls)} tools into {len(stages)} execution stages")
        return stages
    
    async def _execute_one(
        self,
        tool_call: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single tool call.
        
        Args:
            tool_call: Dictionary with 'tool' name and 'params'
        
        Returns:
            Result dictionary with 'success', 'tool', 'result', or 'error'
        """
        tool_name = tool_call.get("tool", "unknown")
        params = tool_call.get("params", {})
        
        try:
            # Import ALL_TOOLS dynamically
            from app.ai_agents.tools import ALL_TOOLS
            
            # Find the tool
            tool = next((t for t in ALL_TOOLS if t.name == tool_name), None)
            
            if not tool:
                return {
                    "success": False,
                    "tool": tool_name,
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": [t.name for t in ALL_TOOLS[:5]]  # Show first 5
                }
            
            # Execute tool
            logger.debug(f"Executing tool: {tool_name}")
            result = await tool.ainvoke(params)
            
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }
    
    async def execute_parallel(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tools with automatic parallelization.
        
        Args:
            tool_calls: List of tool calls [{"tool": "name", "params": {...}}, ...]
        
        Returns:
            List of results in same order as input
        
        Example:
            tool_calls = [
                {"tool": "trace_address", "params": {"address": "0xABC"}},
                {"tool": "risk_score", "params": {"address": "0xABC"}},
                {"tool": "get_labels", "params": {"address": "0xABC"}}
            ]
            
            # Returns 3 results, with risk_score and get_labels executed in parallel
            # after trace_address completes
        """
        if not tool_calls:
            return []
        
        # Analyze dependencies and create execution stages
        stages = self._analyze_dependencies(tool_calls)
        
        logger.info(f"Executing {len(tool_calls)} tools in {len(stages)} stage(s)")
        
        # Execute each stage
        all_results: Dict[str, Dict[str, Any]] = {}
        
        for stage_idx, stage in enumerate(stages):
            logger.debug(f"Stage {stage_idx + 1}/{len(stages)}: {len(stage)} tool(s)")
            
            if len(stage) == 1:
                # Single tool - no need for parallel execution
                result = await self._execute_one(stage[0])
                tool_name = stage[0].get("tool", "")
                all_results[tool_name] = result
            else:
                # Multiple tools - execute in parallel
                tasks = [self._execute_one(tc) for tc in stage]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Store results
                for tool_call, result in zip(stage, results):
                    tool_name = tool_call.get("tool", "")
                    
                    # Handle exceptions
                    if isinstance(result, Exception):
                        all_results[tool_name] = {
                            "success": False,
                            "tool": tool_name,
                            "error": str(result)
                        }
                    else:
                        all_results[tool_name] = result
        
        # Return results in original order
        ordered_results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool", "")
            result = all_results.get(tool_name, {
                "success": False,
                "tool": tool_name,
                "error": "Tool not executed"
            })
            ordered_results.append(result)
        
        return ordered_results
    
    async def execute_batch(
        self,
        tool_calls: List[Dict[str, Any]],
        max_concurrent: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Execute tools in batches with concurrency limit.
        
        Useful for large numbers of tool calls to avoid overwhelming the system.
        
        Args:
            tool_calls: List of tool calls
            max_concurrent: Maximum concurrent executions
        
        Returns:
            List of results
        """
        if not tool_calls:
            return []
        
        results: List[Dict[str, Any]] = []
        
        # Process in batches
        for i in range(0, len(tool_calls), max_concurrent):
            batch = tool_calls[i:i + max_concurrent]
            batch_results = await self.execute_parallel(batch)
            results.extend(batch_results)
        
        return results
    
    def add_dependency(self, tool: str, depends_on: str) -> None:
        """
        Add a tool dependency manually.
        
        Args:
            tool: Tool that has a dependency
            depends_on: Tool it depends on
        
        Example:
            executor.add_dependency("my_tool", "trace_address")
            # Now my_tool will wait for trace_address to complete
        """
        self.dependencies[tool].add(depends_on)
        logger.debug(f"Added dependency: {tool} depends on {depends_on}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics"""
        return {
            "registered_dependencies": len(self.dependencies),
            "total_dependency_edges": sum(len(deps) for deps in self.dependencies.values())
        }


# Global singleton instance
parallel_executor = ParallelToolExecutor()


logger.info("✅ Parallel Tool Executor initialized")
