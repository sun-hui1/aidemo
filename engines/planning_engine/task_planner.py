"""
任务规划器引擎 - 实现 ReAct (Reasoning + Acting) 循环，支持任务分解、自我反思和迭代执行
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class TaskPlanner:
    """任务规划与执行引擎"""
    
    def __init__(self):
        self.max_iterations = 10
        self.current_plan = None

    def create_plan(self, goal: str, context: str = "", max_steps: int = 10) -> Dict[str, Any]:
        """创建任务执行计划"""
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
            
            return {
                "success": True,
                "data": {
                    "plan_id": plan["id"],
                    "goal": goal,
                    "total_steps": len(plan["steps"]),
                    "steps": plan["steps"]
                },
                "message": f"已创建包含 {len(plan['steps'])} 个步骤的执行计划"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_step(self, step_id: int, action: str, 
                     tool_name: Optional[str] = None, 
                     tool_args: Optional[Dict] = None) -> Dict[str, Any]:
        """执行计划中的单个步骤"""
        if not self.current_plan:
            return {"success": False, "error": "没有活跃的计划，请先创建计划"}
        
        try:
            step = None
            for s in self.current_plan["steps"]:
                if s["id"] == step_id:
                    step = s
                    break
            
            if not step:
                return {"success": False, "error": f"未找到步骤 ID: {step_id}"}
            
            step["status"] = "executing"
            step["action"] = action
            step["tool_used"] = tool_name
            step["started_at"] = datetime.now().isoformat()
            
            result_data = {
                "step_id": step_id,
                "action": action,
                "tool": tool_name,
                "status": "ready_for_execution"
            }
            
            step["status"] = "completed"
            step["completed_at"] = datetime.now().isoformat()
            self.current_plan["current_step"] = step_id
            if step_id not in self.current_plan["completed_steps"]:
                self.current_plan["completed_steps"].append(step_id)
            
            return {
                "success": True,
                "data": result_data,
                "message": f"步骤 {step_id} 执行完成：{action}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reflect_and_adjust(self, current_result: str, 
                          obstacles: Optional[List[str]] = None,
                          new_insights: Optional[List[str]] = None) -> Dict[str, Any]:
        """反思当前结果并调整计划"""
        if not self.current_plan:
            return {"success": False, "error": "没有活跃的计划"}
        
        try:
            reflection = {
                "timestamp": datetime.now().isoformat(),
                "current_result": current_result,
                "obstacles": obstacles or [],
                "new_insights": new_insights or [],
                "adjustments_made": []
            }
            
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
            
            if len(obstacles) > 2 or (new_insights and len(new_insights) > 1):
                reflection["recommendation"] = "建议重新规划任务流程"
            
            self.current_plan["reflections"].append(reflection)
            
            return {
                "success": True,
                "data": reflection,
                "message": f"完成反思，识别到 {len(obstacles) if obstacles else 0} 个障碍"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_plan_status(self) -> Dict[str, Any]:
        """获取当前计划状态"""
        if not self.current_plan:
            return {"success": False, "error": "没有活跃的计划"}
        
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
        
        return {
            "success": True,
            "data": status_summary,
            "message": f"计划进度：{completed}/{total_steps} ({progress:.1f}%)"
        }
