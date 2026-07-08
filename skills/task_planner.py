"""
任务规划器技能
实现 ReAct (Reasoning + Acting) 循环，支持任务分解、自我反思和迭代执行
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from base_skill import BaseSkill, SkillResult


class TaskPlanner(BaseSkill):
    """任务规划与执行技能"""
    
    def __init__(self):
        super().__init__(
            name="task_planner",
            description="负责任务分解、规划执行流程、自我反思和迭代优化",
            version="1.0.0"
        )
        self.max_iterations = 10
        self.current_plan = None

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "create_plan",
                "description": "创建详细的任务执行计划，将复杂任务分解为可执行的步骤",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {
                            "type": "string",
                            "description": "要达成的最终目标"
                        },
                        "context": {
                            "type": "string",
                            "description": "当前上下文信息，包括已知条件和约束",
                            "default": ""
                        },
                        "max_steps": {
                            "type": "integer",
                            "description": "最大步骤数，默认 10",
                            "default": 10
                        }
                    },
                    "required": ["goal"]
                }
            },
            {
                "name": "execute_step",
                "description": "执行计划中的单个步骤，并记录结果",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "step_id": {
                            "type": "integer",
                            "description": "步骤 ID"
                        },
                        "action": {
                            "type": "string",
                            "description": "要执行的动作描述"
                        },
                        "tool_name": {
                            "type": "string",
                            "description": "使用的工具名称"
                        },
                        "tool_args": {
                            "type": "object",
                            "description": "工具参数"
                        }
                    },
                    "required": ["step_id", "action"]
                }
            },
            {
                "name": "reflect_and_adjust",
                "description": "反思当前执行结果，调整后续计划",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "current_result": {
                            "type": "string",
                            "description": "当前执行结果"
                        },
                        "obstacles": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "遇到的障碍列表"
                        },
                        "new_insights": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "新的发现或洞察"
                        }
                    },
                    "required": ["current_result"]
                }
            },
            {
                "name": "get_plan_status",
                "description": "获取当前计划的执行状态",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    def create_plan(self, goal: str, context: str = "", max_steps: int = 10) -> SkillResult:
        """
        创建任务执行计划
        注意：实际 AI Agent 中，这里会调用 LLM 进行智能规划
        当前版本提供基础框架，规划逻辑需要结合 LLM 实现
        """
        try:
            plan = {
                "id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "goal": goal,
                "context": context,
                "created_at": datetime.now().isoformat(),
                "status": "created",
                "steps": [],
                "current_step": 0,
                "completed_steps": [],
                "failed_steps": [],
                "reflections": [],
                "max_steps": max_steps
            }
            
            # 基础任务分解示例（实际应由 LLM 生成）
            if "文件" in goal or "创建" in goal:
                plan["steps"] = [
                    {"id": 1, "action": "分析需求，确定文件内容和结构", "status": "pending"},
                    {"id": 2, "action": "检查目标目录是否存在", "status": "pending"},
                    {"id": 3, "action": "创建或修改文件", "status": "pending"},
                    {"id": 4, "action": "验证文件内容是否正确", "status": "pending"},
                    {"id": 5, "action": "总结完成情况", "status": "pending"}
                ]
            elif "代码" in goal or "执行" in goal:
                plan["steps"] = [
                    {"id": 1, "action": "理解代码需求和功能", "status": "pending"},
                    {"id": 2, "action": "编写或准备代码", "status": "pending"},
                    {"id": 3, "action": "在沙箱中执行代码", "status": "pending"},
                    {"id": 4, "action": "分析执行结果", "status": "pending"},
                    {"id": 5, "action": "修复错误或优化代码", "status": "pending"}
                ]
            else:
                plan["steps"] = [
                    {"id": 1, "action": "分析任务需求", "status": "pending"},
                    {"id": 2, "action": "制定执行策略", "status": "pending"},
                    {"id": 3, "action": "执行主要任务", "status": "pending"},
                    {"id": 4, "action": "验证结果", "status": "pending"},
                    {"id": 5, "action": "完成任务", "status": "pending"}
                ]
            
            self.current_plan = plan
            
            return SkillResult(
                success=True,
                data={
                    "plan_id": plan["id"],
                    "goal": goal,
                    "total_steps": len(plan["steps"]),
                    "steps": plan["steps"]
                },
                error=None,
                message=f"已创建包含 {len(plan['steps'])} 个步骤的执行计划"
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="创建计划失败"
            )

    def execute_step(self, step_id: int, action: str, 
                     tool_name: Optional[str] = None, 
                     tool_args: Optional[Dict] = None) -> SkillResult:
        """
        执行计划中的单个步骤
        """
        if not self.current_plan:
            return SkillResult(
                success=False,
                data=None,
                error="没有活跃的计划，请先创建计划",
                message="需要先调用 create_plan 创建任务计划"
            )
        
        try:
            # 查找步骤
            step = None
            for s in self.current_plan["steps"]:
                if s["id"] == step_id:
                    step = s
                    break
            
            if not step:
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"未找到步骤 ID: {step_id}",
                    message="请检查步骤 ID 是否正确"
                )
            
            # 更新步骤状态
            step["status"] = "executing"
            step["action"] = action
            step["tool_used"] = tool_name
            step["started_at"] = datetime.now().isoformat()
            
            # 这里应该调用实际的技能系统执行工具
            # 当前版本仅做记录，实际执行由外部协调
            result_data = {
                "step_id": step_id,
                "action": action,
                "tool": tool_name,
                "status": "ready_for_execution",
                "message": "步骤已准备就绪，等待外部执行器调用相应工具"
            }
            
            step["status"] = "completed"
            step["completed_at"] = datetime.now().isoformat()
            self.current_plan["current_step"] = step_id
            if step_id not in self.current_plan["completed_steps"]:
                self.current_plan["completed_steps"].append(step_id)
            
            return SkillResult(
                success=True,
                data=result_data,
                error=None,
                message=f"步骤 {step_id} 执行完成：{action}"
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="执行步骤失败"
            )

    def reflect_and_adjust(self, current_result: str, 
                          obstacles: Optional[List[str]] = None,
                          new_insights: Optional[List[str]] = None) -> SkillResult:
        """
        反思当前结果并调整计划
        """
        if not self.current_plan:
            return SkillResult(
                success=False,
                data=None,
                error="没有活跃的计划",
                message="需要先创建计划才能进行反思"
            )
        
        try:
            reflection = {
                "timestamp": datetime.now().isoformat(),
                "current_result": current_result,
                "obstacles": obstacles or [],
                "new_insights": new_insights or [],
                "adjustments_made": []
            }
            
            # 根据反思调整后续步骤
            adjustments = []
            if obstacles:
                for obstacle in obstacles:
                    if "文件不存在" in obstacle:
                        adjustments.append("添加检查目录/文件存在的步骤")
                    elif "权限" in obstacle:
                        adjustments.append("检查并请求必要权限")
                    elif "格式错误" in obstacle:
                        adjustments.append("增加数据验证步骤")
            
            reflection["adjustments_made"] = adjustments
            
            # 如果有重大调整，可以重新规划
            if len(obstacles) > 2 or (new_insights and len(new_insights) > 1):
                reflection["recommendation"] = "建议重新规划任务流程"
            
            self.current_plan["reflections"].append(reflection)
            
            return SkillResult(
                success=True,
                data=reflection,
                error=None,
                message=f"完成反思，识别到 {len(obstacles) if obstacles else 0} 个障碍，{len(new_insights) if new_insights else 0} 个新发现"
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                data=None,
                error=str(e),
                message="反思过程失败"
            )

    def get_plan_status(self) -> SkillResult:
        """
        获取当前计划状态
        """
        if not self.current_plan:
            return SkillResult(
                success=False,
                data=None,
                error="没有活跃的计划",
                message="请先创建计划"
            )
        
        total_steps = len(self.current_plan["steps"])
        completed = len(self.current_plan["completed_steps"])
        progress = (completed / total_steps * 100) if total_steps > 0 else 0
        
        status_summary = {
            "plan_id": self.current_plan["id"],
            "goal": self.current_plan["goal"],
            "total_steps": total_steps,
            "completed_steps": completed,
            "progress_percent": round(progress, 2),
            "current_status": self.current_plan["status"],
            "reflections_count": len(self.current_plan["reflections"]),
            "steps_detail": self.current_plan["steps"]
        }
        
        return SkillResult(
            success=True,
            data=status_summary,
            error=None,
            message=f"计划进度：{completed}/{total_steps} ({progress:.1f}%)"
        )

    def call(self, tool_name: str, **kwargs) -> SkillResult:
        if tool_name == "create_plan":
            return self.create_plan(
                goal=kwargs.get("goal", ""),
                context=kwargs.get("context", ""),
                max_steps=kwargs.get("max_steps", 10)
            )
        elif tool_name == "execute_step":
            return self.execute_step(
                step_id=kwargs.get("step_id"),
                action=kwargs.get("action", ""),
                tool_name=kwargs.get("tool_name"),
                tool_args=kwargs.get("tool_args")
            )
        elif tool_name == "reflect_and_adjust":
            return self.reflect_and_adjust(
                current_result=kwargs.get("current_result", ""),
                obstacles=kwargs.get("obstacles"),
                new_insights=kwargs.get("new_insights")
            )
        elif tool_name == "get_plan_status":
            return self.get_plan_status()
        else:
            return SkillResult(
                success=False,
                data=None,
                error=f"未知工具：{tool_name}",
                message=f"{self.name} 技能不包含此工具"
            )
