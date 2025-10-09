from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import time
import json
import requests
import math # Added for math.radians
import os # Added for os.getenv
import agents

class DanceMessage(BaseModel):
    """舞蹈消息 - 用于Agent之间的通信"""
    message_id: str = Field(..., description="消息唯一标识")
    sender: str = Field(..., description="发送者Agent名称")
    receiver: Optional[str] = Field(None, description="接收者Agent名称，None为广播")
    stage: str = Field(..., description="任务阶段，如参数计算、建模、装配、验证等")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(..., description="消息类型：TASK_REQUEST, TASK_UPDATE, TASK_RESULT等")
    input_summary: Optional[Dict[str, Any]] = Field(None, description="输入参数摘要")
    output_summary: Optional[Dict[str, Any]] = Field(None, description="输出数据摘要")
    quality: Optional[Dict[str, Any]] = Field(None, description="执行质量指标，如置信度等")
    message_status: str = Field(..., description="消息状态，如SENT、READ、PROCESSED")
    related_task_id: Optional[str] = Field(None, description="关联的任务ID")
    suggestion: Optional[str] = Field(None, description="下游触发建议或反馈")
    pheromone: Optional[float] = Field(1.0, description="信息素浓度，默认1.0")
    timestamp: Optional[str] = Field(None, description="消息生成时间")

class TaskAnnouncement(BaseModel):
    """任务公告(RFP) - 用于描述要执行的工作"""
    task_id: str = Field(..., description="任务唯一标识")
    task_name: str = Field(..., description="任务名称")
    description: str = Field(..., description="任务描述")
    inputs: Dict[str, Any] = Field(..., description="输入参数向量")
    deliverable: str = Field(..., description="期望的输出格式")
    deadline: str = Field(..., description="完成时限")
    assigned_agent: Optional[str] = Field(None, description="已分配的Agent")
    task_status: str = Field(default="PENDING", description="任务状态：PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, FAILED")
    created_by: str = Field(..., description="创建任务的Agent")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="任务创建时间")

class TaskBoard:
    """任务公告板 - 管理所有待分配的任务"""
    
    def __init__(self):
        self.pending_tasks: Dict[str, Dict] = {}
        self.completed_tasks: Dict[str, TaskAnnouncement] = {}
        self.messages: List[DanceMessage] = []  # 存储所有消息
        self.scheduler_bee = None  # 对调度蜂的引用
    
    def post_task(self, task: TaskAnnouncement) -> str:
        """发布新任务到公告板"""
        self.pending_tasks[task.task_id] = {
            "task": task,
            "proposals": [],
            "messages": []
        }
        return f"任务 {task.task_id} 已发布到公告板"
    
    def get_pending_tasks(self) -> List[TaskAnnouncement]:
        """获取所有待分配的任务"""
        return [data["task"] for data in self.pending_tasks.values() if data["task"].task_status == "PENDING"]
    
    def get_all_tasks(self) -> List[TaskAnnouncement]:
        """获取所有任务（包括已分配的）"""
        return [data["task"] for data in self.pending_tasks.values()]
    
    def assign_task(self, task_id: str, agent_name: str) -> bool:
        """分配任务给指定Agent"""
        if task_id in self.pending_tasks:
            self.pending_tasks[task_id]["task"].assigned_agent = agent_name
            self.pending_tasks[task_id]["task"].task_status = "ASSIGNED"
            return True
        return False
    
    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """更新任务状态"""
        if task_id in self.pending_tasks:
            self.pending_tasks[task_id]["task"].task_status = new_status
            if new_status == "COMPLETED":
                task_data = self.pending_tasks.pop(task_id)
                self.completed_tasks[task_id] = task_data["task"]
            return True
        return False
    
    def submit_proposal(self, task_id: str, proposal: Any) -> bool:
        """提交任务提案"""
        if task_id in self.pending_tasks:
            self.pending_tasks[task_id]["proposals"].append(proposal)
            print(f"   存储提案: {proposal.agent_name} -> {proposal.proposal_id}")
            return True
        return False
    
    def get_task_proposals(self, task_id: str) -> List[Any]:
        """获取任务的提案列表"""
        if task_id in self.pending_tasks:
            return self.pending_tasks[task_id]["proposals"]
        return []
    
    def add_message(self, message: DanceMessage):
        """添加消息到公告板"""
        self.messages.append(message)
        # 如果消息关联了任务，也添加到任务的对话中
        if message.related_task_id and message.related_task_id in self.pending_tasks:
            self.pending_tasks[message.related_task_id]["messages"].append(message)
    
    def get_task_messages(self, task_id: str) -> List[DanceMessage]:
        """获取任务的对话消息"""
        if task_id in self.pending_tasks:
            return self.pending_tasks[task_id]["messages"]
        return []

class TaskProposal(BaseModel):
    """任务提案 - 工蜂提交的竞标提案"""
    proposal_id: str = Field(..., description="提案唯一标识")
    task_id: str = Field(..., description="目标任务ID")
    agent_name: str = Field(..., description="提交提案的Agent名称")
    role_declaration: str = Field(..., description="角色与技能声明")
    execution_plan: str = Field(..., description="执行计划与关键步骤")
    confidence: str = Field(..., description="置信度：高/中/低")
    estimated_time: str = Field(..., description="预估执行时间")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="提案提交时间")

class TaskDAG:
    """任务依赖关系图 - 管理任务的逻辑依赖"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskAnnouncement] = {}
        self.dependencies: Dict[str, List[str]] = {}  # task_id -> [依赖的任务ID列表]
        self.dependents: Dict[str, List[str]] = {}    # task_id -> [被依赖的任务ID列表]
    
    def add_task(self, task: TaskAnnouncement, dependencies: List[str] = None):
        """添加任务到DAG"""
        if dependencies is None:
            dependencies = []
        
        self.tasks[task.task_id] = task
        self.dependencies[task.task_id] = dependencies
        
        # 更新被依赖关系
        for dep_id in dependencies:
            if dep_id not in self.dependents:
                self.dependents[dep_id] = []
            self.dependents[dep_id].append(task.task_id)
    
    def get_ready_tasks(self) -> List[str]:
        """获取可以执行的任务（无依赖或依赖已完成）"""
        ready_tasks = []
        for task_id, deps in self.dependencies.items():
            if not deps:  # 无依赖
                ready_tasks.append(task_id)
            else:
                # 检查依赖是否都已完成
                all_deps_completed = True
                for dep_id in deps:
                    if dep_id in self.tasks and self.tasks[dep_id].task_status != "COMPLETED":
                        all_deps_completed = False
                        break
                if all_deps_completed:
                    ready_tasks.append(task_id)
        return ready_tasks
    
    def get_task_dependencies(self, task_id: str) -> List[str]:
        """获取任务的依赖列表"""
        return self.dependencies.get(task_id, [])
    
    def get_task_dependents(self, task_id: str) -> List[str]:
        """获取依赖此任务的任务列表"""
        return self.dependents.get(task_id, [])
    
    def get_dependencies(self, task_id: str) -> List[str]:
        """获取指定任务的依赖任务ID列表"""
        if task_id in self.dependencies:
            return self.dependencies[task_id]
        return []
    
    def get_dependent_tasks(self, task_id: str) -> List[str]:
        """获取依赖于指定任务的任务ID列表"""
        dependent_tasks = []
        for task, deps in self.dependencies.items():
            if task_id in deps:
                dependent_tasks.append(task)
        return dependent_tasks



class BeeAgent:
    """工蜂基类 - 所有工蜂的基础"""
    
    def __init__(self, name: str, capabilities: List[str], task_board: TaskBoard):
        self.name = name
        self.capabilities = capabilities
        self.task_board = task_board
        self.current_task: Optional[str] = None
    
    def view_tasks(self) -> List[TaskAnnouncement]:
        """查看可用的任务"""
        return self.task_board.get_pending_tasks()
    
    def submit_proposal(self, task_id: str, execution_plan: str, confidence: str = "中", estimated_time: str = "15分钟") -> bool:
        """提交任务提案"""
        proposal = TaskProposal(
            proposal_id=f"PROP-{str(uuid.uuid4())[:8].upper()}",
            task_id=task_id,
            agent_name=self.name,
            role_declaration=f"我是{self.name}，擅长{', '.join(self.capabilities)}",
            execution_plan=execution_plan,
            confidence=confidence,
            estimated_time=estimated_time
        )
        
        success = self.task_board.submit_proposal(task_id, proposal)
        if success:
            print(f"✅ {self.name} 已提交提案: {proposal.proposal_id}")
        return success
    
    def send_message(self, content: str, stage: str, message_type: str = "TASK_UPDATE", 
                    receiver: Optional[str] = None, related_task_id: Optional[str] = None):
        """发送消息"""
        message = DanceMessage(
            message_id=str(uuid.uuid4()),
            sender=self.name,
            receiver=receiver,
            stage=stage,
            content=content,
            message_type=message_type,
            message_status="SENT",
            related_task_id=related_task_id,
            timestamp=datetime.now().isoformat()
        )
        
        self.task_board.add_message(message)
        return message

class SmartBeeAgent(BeeAgent):
    """智能工蜂 - 简化版本，适合Dify API化"""
    
    def __init__(self, name: str, capabilities: List[str], task_board: TaskBoard):
        super().__init__(name, capabilities, task_board)
        self.task_history: List[str] = []  # 任务执行历史
        self.current_task: Optional[str] = None  # 当前执行的任务ID
    
    def execute_task(self, task_id: str) -> bool:
        """执行分配到的任务"""
        if not self.current_task:
            self.current_task = task_id
        
        # 获取任务详情
        task = self._get_task_by_id(task_id)
        if not task:
            print(f"❌ {self.name}: 未找到任务 {task_id}")
            return False
        
        print(f"\n🚀 {self.name} 开始执行任务: {task.task_name}")
        print(f"   任务描述: {task.description}")
        print(f"   输入参数: {task.inputs}")
        
        # 通知调度蜂任务开始执行
        if hasattr(self.task_board, 'scheduler_bee'):
            self.task_board.scheduler_bee.active_tasks[task_id] = self.name
        
        try:
            # 根据任务类型执行相应的处理逻辑
            if "参数分析" in task.task_name or "需求分析" in task.task_name:
                result = self._execute_parameter_analysis(task)
            elif "3D建模" in task.task_name:
                result = self._execute_3d_modeling(task)
            elif "装配设计" in task.task_name:
                result = self._execute_assembly_design(task)
            else:
                result = self._execute_generic_task(task)
            
            if result:
                # 更新任务状态为完成
                self.task_board.update_task_status(task_id, "COMPLETED")
                print(f"✅ {self.name} 完成任务: {task.task_name}")
                
                # 发送任务完成消息
                self.send_message(
                    f"任务执行完成！生成结果：{result.get('summary', '无')}",
                    "任务完成",
                    "TASK_RESULT",
                    related_task_id=task_id
                )
                
                # 从调度蜂的active_tasks中移除
                if hasattr(self.task_board, 'scheduler_bee') and task_id in self.task_board.scheduler_bee.active_tasks:
                    del self.task_board.scheduler_bee.active_tasks[task_id]
                
                # 清理当前任务
                self.current_task = None
                return True
            else:
                print(f"❌ {self.name} 任务执行失败: {task.task_name}")
                self.task_board.update_task_status(task_id, "FAILED")
                
                # 从调度蜂的active_tasks中移除
                if hasattr(self.task_board, 'scheduler_bee') and task_id in self.task_board.scheduler_bee.active_tasks:
                    del self.task_board.scheduler_bee.active_tasks[task_id]
                
                return False
                
        except Exception as e:
            print(f"❌ {self.name} 任务执行异常: {e}")
            self.task_board.update_task_status(task_id, "FAILED")
            
            # 从调度蜂的active_tasks中移除
            if hasattr(self.task_board, 'scheduler_bee') and task_id in self.task_board.scheduler_bee.active_tasks:
                del self.task_board.scheduler_bee.active_tasks[task_id]
            
            self.current_task = None
            return False
    
    def _get_task_by_id(self, task_id: str) -> Optional[TaskAnnouncement]:
        """根据任务ID获取任务详情"""
        all_tasks = self.task_board.get_all_tasks()
        for task in all_tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def _execute_parameter_analysis(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """执行参数分析任务 - 工况分析蜂的核心功能"""
        # 导入工况分析蜂模块
        try:
            from bee_mas.agents.parameter_analysis_bee import ParameterAnalysisBee
        except ImportError:
            from agents.parameter_analysis_bee import ParameterAnalysisBee
        bee = ParameterAnalysisBee(self.task_board)
        return bee._execute_parameter_analysis(task)
    
    def _execute_3d_modeling(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """执行3D建模任务 - 三维建模蜂的核心功能"""
        # 导入三维建模蜂模块
        try:
            from bee_mas.agents.modeling_bee import ModelingBee
        except ImportError:
            from agents.modeling_bee import ModelingBee
        bee = ModelingBee(self.task_board)
        return bee._execute_3d_modeling(task)
    
    def _execute_assembly_design(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """执行装配设计任务 - 装配蜂的核心功能"""
        # 导入装配蜂模块
        try:
            from bee_mas.agents.assembly_bee import AssemblyBee
        except ImportError:
            from agents.assembly_bee import AssemblyBee
        bee = AssemblyBee(self.task_board)
        return bee._execute_assembly_design(task)
    
    
    def _execute_generic_task(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """执行通用任务"""
        print(f"   📝 {self.name} 开始执行通用任务...")
        return {
            "task_id": task.task_id,
            "agent_name": self.name,
            "execution_time": datetime.now().isoformat(),
            "result_type": "通用任务结果",
            "summary": f"通用任务 '{task.task_name}' 完成",
            "is_fallback": True
        }
    
    def get_assigned_tasks(self) -> List[TaskAnnouncement]:
        """获取分配给自己的任务"""
        all_tasks = self.task_board.get_all_tasks()
        return [task for task in all_tasks if task.assigned_agent == self.name and task.task_status == "ASSIGNED"]
    
    def work_on_assigned_tasks(self):
        """处理分配给自己的任务"""
        assigned_tasks = self.get_assigned_tasks()
        if not assigned_tasks:
            print(f"🤖 {self.name}: 没有分配的任务")
            return
        
        print(f"\n🤖 {self.name} 开始处理分配的任务...")
        for task in assigned_tasks:
            print(f"   处理任务: {task.task_name} ({task.task_id})")
            # 更新任务状态为IN_PROGRESS
            self.task_board.update_task_status(task.task_id, "IN_PROGRESS")
            success = self.execute_task(task.task_id)
            if success:
                print(f"   ✅ 任务 {task.task_name} 执行成功")
            else:
                print(f"   ❌ 任务 {task.task_name} 执行失败")
            print()  # 空行分隔
    
    def analyze_task(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """分析任务，判断是否适合执行"""
        # 基于关键词匹配的简单分析
        task_desc = task.description.lower()
        capabilities_str = " ".join(self.capabilities).lower()
        
        # 计算匹配度
        match_score = 0
        for cap in self.capabilities:
            if cap.lower() in task_desc:
                match_score += 1
        
        suitable = match_score > 0
        confidence = "高" if match_score >= 2 else "中" if match_score >= 1 else "低"
        
        return {
            "suitable": suitable,
            "confidence": confidence,
            "reasoning": f"基于能力匹配分析，匹配度：{match_score}/{len(self.capabilities)}",
            "estimated_time": "15分钟",
            "execution_plan": f"采用标准流程执行{task.task_name}任务",
            "risks": "无明显风险"
        }
    
    def generate_proposal(self, task: TaskAnnouncement) -> TaskProposal:
        """生成提案"""
        # 分析任务
        analysis = self.analyze_task(task)
        
        if not analysis.get("suitable", False):
            # 如果不适合，不提交提案
            print(f"❌ {self.name} 认为不适合执行任务 {task.task_name}")
            return None
        
        # 生成提案
        proposal = TaskProposal(
            proposal_id=f"PROP-{str(uuid.uuid4())[:8].upper()}",
            task_id=task.task_id,
            agent_name=self.name,
            role_declaration=f"我是{self.name}，专业从事{', '.join(self.capabilities)}工作",
            execution_plan=analysis.get("execution_plan", "采用标准流程执行任务"),
            confidence=analysis.get("confidence", "中"),
            estimated_time=analysis.get("estimated_time", "15分钟"),
            timestamp=datetime.now().isoformat()
        )
        
        # 提交提案
        if self.task_board.submit_proposal(task.task_id, proposal):
            print(f"✅ {self.name} 已提交提案: {proposal.proposal_id}")
            print(f"   置信度: {proposal.confidence}, 预估时间: {proposal.estimated_time}")
            return proposal
        else:
            print(f"❌ 提案提交失败")
            return None
    
    def auto_bid_on_tasks(self):
        """自动竞标适合的任务（基于LLM API）"""
        available_tasks = self.view_tasks()
        if not available_tasks:
            return
        
        print(f"\n🤖 {self.name} 开始自动任务分析...")
        
        for task in available_tasks:
            if task.task_status == "PENDING" and not task.assigned_agent:
                # 检查是否已经有提案
                existing_proposals = self.task_board.get_task_proposals(task.task_id)
                has_my_proposal = any(p.agent_name == self.name for p in existing_proposals)
                
                if has_my_proposal:
                    print(f"   跳过任务: {task.task_name} (已有我的提案)")
                    continue
                
                print(f"   分析任务: {task.task_name}")
                proposal = self.generate_llm_proposal(task)
                if proposal:
                    self.task_history.append(task.task_id)
                    print(f"   ✅ 已提交提案")
                else:
                    print(f"   ❌ 不适合此任务")
    
    def generate_llm_proposal(self, task: TaskAnnouncement) -> Optional[TaskProposal]:
        """基于LLM API生成任务提案"""
        try:
            # 构建系统提示词
            system_prompt = f"""你是一个专业的{self.name}，负责分析任务并生成提案。

你的专业能力包括: {', '.join(self.capabilities)}

请分析以下任务，判断你是否适合执行该任务。如果适合，请生成一个详细的提案。

返回格式必须是有效的JSON，包含以下结构：
{{
    "suitable": true/false,
    "confidence": "高/中/低",
    "reasoning": "详细理由",
    "estimated_time": "预估时间（分钟）",
    "execution_plan": "详细执行计划",
    "risks": "风险评估"
}}

如果你认为不适合执行该任务，请将suitable设为false，其他字段可以为空。"""

            # 构建用户提示词
            user_prompt = f"""请分析以下任务并生成提案：

任务信息：
- 任务名称: {task.task_name}
- 任务描述: {task.description}
- 期望交付物: {task.deliverable}
- 完成时限: {task.deadline}

输入参数: {task.inputs}

请基于你的专业能力({', '.join(self.capabilities)})，分析你是否适合执行此任务，并提供详细的提案。"""
            
            # 调用DeepSeek API
            deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
            deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            deepseek_api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
            
            if not deepseek_api_key:
                raise ValueError("未配置DEEPSEEK_API_KEY，无法使用LLM API生成提案")
            
            headers = {
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": deepseek_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(deepseek_api_url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            
            # 解析响应
            import re
            json_match = re.search(r'\{.*\}', answer, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                proposal_data = json.loads(json_str)
            else:
                proposal_data = json.loads(answer)
            
            # 检查是否适合执行任务
            if not proposal_data.get("suitable", False):
                print(f"   ❌ {self.name} 认为不适合执行任务 {task.task_name}")
                return None
            
            # 生成提案
            proposal = TaskProposal(
                proposal_id=f"PROP-{str(uuid.uuid4())[:8].upper()}",
                task_id=task.task_id,
                agent_name=self.name,
                role_declaration=f"我是{self.name}，专业从事{', '.join(self.capabilities)}工作",
                execution_plan=proposal_data.get("execution_plan", "采用标准流程执行任务"),
                confidence=proposal_data.get("confidence", "中"),
                estimated_time=f"{proposal_data.get('estimated_time', 15)}分钟",
                timestamp=datetime.now().isoformat()
            )
            
            # 提交提案
            if self.task_board.submit_proposal(task.task_id, proposal):
                print(f"   ✅ {self.name} 已提交提案: {proposal.proposal_id}")
                print(f"   理由: {proposal_data.get('reasoning', '无')}")
                print(f"   置信度: {proposal.confidence}, 预估时间: {proposal.estimated_time}")
                return proposal
            else:
                print(f"   ❌ 提案提交失败")
                return None
                
        except Exception as e:
            print(f"   ❌ LLM提案生成失败: {e}")
            raise

class SchedulerBee(BeeAgent):
    """调度蜂 - 负责任务分解、分配和监控（基于LLM API）"""
    
    def __init__(self, task_board: TaskBoard, task_dag: TaskDAG):
        super().__init__("调度蜂", ["任务分解", "任务分配", "进度监控", "质量评估"], task_board)
        self.task_dag = task_dag
        self.active_tasks: Dict[str, str] = {}  # task_id -> agent_name
        self.task_queue: List[str] = []  # 任务队列
        self.registered_agents: List[BeeAgent] = []  # 注册的智能工蜂列表
        
        # 设置TaskBoard对调度蜂的引用
        task_board.scheduler_bee = self
        
        # DeepSeek API配置
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.deepseek_api_url = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
    
    def register_agent(self, agent: BeeAgent) -> bool:
        """注册智能工蜂到调度蜂"""
        if agent not in self.registered_agents:
            self.registered_agents.append(agent)
            print(f"✅ 已注册智能工蜂: {agent.name}")
            return True
        return False
    
    def decompose_task(self, task_description: str, inputs: Dict[str, Any] = None) -> List[TaskAnnouncement]:
        """使用LLM智能分解复杂任务为子任务（完全基于prompt）"""
        if inputs is None:
            inputs = {}
        
        print(f"\n🧠 调度蜂开始智能任务分解...")
        print(f"   原始任务: {task_description}")
        
        # 构建系统提示词
        system_prompt = """你是一个专业的任务分解专家，负责将复杂的设计任务分解为一系列可执行的子任务。

你的任务是分析用户的需求，并将其分解为适合不同专业工蜂执行的子任务序列。

系统中有以下专业工蜂：
1. 工况分析蜂 - 负责需求分析和参数计算
2. 三维建模蜂 - 负责3D建模和OpenSCAD代码生成
3. 装配蜂 - 负责装配设计和空间定位

请根据任务类型，合理分解为2-4个子任务，确保任务之间的逻辑顺序和依赖关系正确。

返回格式必须是有效的JSON，包含以下结构：
{
    "subtasks": [
        {
            "name": "子任务名称",
            "description": "子任务描述",
            "estimated_time": "预估时间（分钟）",
            "deliverable": "交付物",
            "dependencies": ["依赖的任务索引（从0开始）"]
        }
    ]
}"""

        # 构建用户提示词
        user_prompt = f"""请将以下任务分解为适合的子任务序列：

任务描述: {task_description}
输入参数: {inputs}

请分析任务类型，并按照工程设计的标准流程进行分解。考虑任务之间的逻辑依赖关系。"""
        
        try:
            # 调用DeepSeek API进行任务分解
            response = self._call_deepseek_api(system_prompt, user_prompt)
            subtasks_data = self._parse_deepseek_response(response)
            
            # 创建子任务列表
            subtasks = []
            task_mapping = {}  # 用于建立依赖关系
            
            for i, subtask_data in enumerate(subtasks_data.get("subtasks", [])):
                task_id = f"TASK-{str(uuid.uuid4())[:8].upper()}"
                task_mapping[i] = task_id
                
                subtask = TaskAnnouncement(
                    task_id=task_id,
                    task_name=subtask_data.get("name", f"子任务{i+1}"),
                    description=subtask_data.get("description", "待补充描述"),
                    inputs=inputs,
                    deliverable=subtask_data.get("deliverable", "交付物"),
                    deadline=f"{subtask_data.get('estimated_time', '30')}分钟",
                    created_by=self.name
                )
                subtasks.append(subtask)
                
                # 发布任务到公告板
                self.task_board.post_task(subtask)
                print(f"   ✅ 已创建子任务: {subtask.task_name} ({task_id}) - {subtask_data.get('assigned_agent', '未指定')}")
            
            # 建立任务依赖关系
            for i, subtask_data in enumerate(subtasks_data.get("subtasks", [])):
                dependencies = subtask_data.get("dependencies", [])
                if dependencies:
                    # 将索引转换为实际的task_id
                    actual_dependencies = []
                    for dep in dependencies:
                        if isinstance(dep, int) and dep < len(subtasks):
                            actual_dependencies.append(task_mapping[dep])
                    
                    if actual_dependencies:
                        self.task_dag.add_task(subtasks[i], actual_dependencies)
            
            print(f"\n📋 智能任务分解完成，共生成 {len(subtasks)} 个子任务")
            return subtasks
            
        except Exception as e:
            print(f"❌ LLM任务分解失败: {str(e)}")
            raise
    
    def _call_deepseek_api(self, system_prompt: str, user_prompt: str) -> str:
        """调用DeepSeek API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.deepseek_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(self.deepseek_api_url, json=data, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            print(f"❌ DeepSeek API调用失败: {str(e)}")
            raise
    
    def _parse_deepseek_response(self, response: str) -> Dict[str, Any]:
        """解析DeepSeek响应"""
        try:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试解析整个响应
                try:
                    return json.loads(response)
                except:
                    raise ValueError("响应中未找到有效的JSON格式")
        except Exception as e:
            print(f"❌ DeepSeek响应解析失败: {str(e)}")
            print(f"原始响应: {response[:200]}...")
            raise
    
    
    def publish_tasks(self, task_description: str, inputs: Dict[str, Any] = None) -> bool:
        """发布新任务并开始竞标流程（基于LLM API）"""
        if inputs is None:
            inputs = {}
        
        print(f"\n📢 调度蜂发布新任务...")
        print(f"   任务描述: {task_description}")
        print(f"   输入参数: {inputs}")
        
        # 分解任务
        subtasks = self.decompose_task(task_description, inputs)
        
        if not subtasks:
            print("❌ 任务分解失败")
            return False
        
        # 通知所有工蜂有新任务
        self.send_message(
            f"新任务已发布：{task_description}，共 {len(subtasks)} 个子任务",
            "任务发布",
            "TASK_REQUEST",
            related_task_id=subtasks[0].task_id
        )
        
        # 触发工蜂竞标过程
        self.trigger_bidding_process(task_description, inputs)
        
        # 等待提案（简化处理）
        print("\n⏳ 等待工蜂提交提案...")
        time.sleep(10)  # 给工蜂时间提交提案
        
        # 评估提案并分配任务
        for task in subtasks:
            self.evaluate_and_assign_task(task.task_id)
        
        return True
    
    def evaluate_and_assign_task(self, task_id: str) -> bool:
        """使用LLM智能评估提案并分配任务（完全基于prompt）"""
        proposals = self.task_board.get_task_proposals(task_id)
        
        if not proposals:
            print(f"   ⚠️ 任务 {task_id} 没有收到提案")
            return False
        
        print(f"\n🧠 调度蜂开始智能提案评估...")
        print(f"   任务ID: {task_id}")
        print(f"   收到提案数量: {len(proposals)}")
        
        # 获取任务详情
        task = self._get_task_by_id(task_id)
        if not task:
            print(f"   ❌ 未找到任务详情")
            return False
        
        # 构建系统提示词
        system_prompt = """你是一个专业的任务分配专家，负责评估工蜂提交的任务提案并选择最佳的执行者。

你的评估标准包括：
1. 提案者的专业能力与任务匹配度
2. 执行计划的合理性和可行性
3. 置信度等级
4. 预估完成时间
5. 角色声明的专业性

请仔细分析每个提案，并选择最适合执行该任务的工蜂。

返回格式必须是有效的JSON，包含以下结构：
{
    "best_proposal_index": 提案索引（从0开始）,
    "evaluation_reasoning": "详细评估理由",
    "risk_assessment": "风险评估",
    "execution_strategy": "执行策略建议"
}"""

        # 构建用户提示词
        user_prompt = f"""请评估以下任务的提案并选择最佳执行者：

任务信息：
- 任务名称: {task.task_name}
- 任务描述: {task.description}
- 期望交付物: {task.deliverable}
- 完成时限: {task.deadline}

提案列表：
"""
        
        for i, proposal in enumerate(proposals):
            user_prompt += f"""
提案 {i+1}:
- 提案ID: {proposal.proposal_id}
- 提交者: {proposal.agent_name}
- 角色声明: {proposal.role_declaration}
- 执行计划: {proposal.execution_plan}
- 置信度: {proposal.confidence}
- 预估时间: {proposal.estimated_time}
"""
        
        user_prompt += """

请基于以上信息，选择最佳提案并提供详细评估。"""
        
        # 调用DeepSeek API进行提案评估
        response = self._call_deepseek_api(system_prompt, user_prompt)
        evaluation_result = self._parse_deepseek_response(response)
        
        best_index = evaluation_result.get("best_proposal_index", 0)
        if 0 <= best_index < len(proposals):
            best_proposal = proposals[best_index]
            
            print(f"   📊 LLM评估结果:")
            print(f"      最佳提案: {best_proposal.agent_name} ({best_proposal.proposal_id})")
            print(f"      评估理由: {evaluation_result.get('evaluation_reasoning', '无')}")
            print(f"      风险评估: {evaluation_result.get('risk_assessment', '无')}")
            
            # 分配任务给最佳提案者
            success = self.assign_task(task_id, best_proposal.agent_name)
            if success:
                print(f"   ✅ 任务已智能分配给 {best_proposal.agent_name}")
                
                # 通知中标者，包含LLM的评估建议
                self.send_message(
                    f"恭喜！您获得了任务 {task_id}。\n评估理由：{evaluation_result.get('evaluation_reasoning', '无')}\n执行策略：{evaluation_result.get('execution_strategy', '标准流程')}",
                    "任务分配",
                    "TASK_UPDATE",
                    receiver=best_proposal.agent_name,
                    related_task_id=task_id
                )
                
                # 立即通知中标Agent开始执行任务
                for agent in self.registered_agents:
                    if agent.name == best_proposal.agent_name and hasattr(agent, 'work_on_assigned_tasks'):
                        try:
                            print(f"   📢 通知 {agent.name} 开始执行任务...")
                            agent.work_on_assigned_tasks()
                        except Exception as e:
                            print(f"   ❌ {agent.name} 执行任务失败: {e}")
                        break
                
                return True
        else:
            print(f"   ❌ LLM评估结果无效，索引超出范围")
            raise ValueError("LLM评估返回的索引超出范围")
        
        return False
    
    def trigger_bidding_process(self, task_description: str, inputs: Dict[str, Any] = None) -> bool:
        """触发工蜂竞标过程（基于LLM API）"""
        if inputs is None:
            inputs = {}
        
        print(f"\n📢 调度蜂触发工蜂竞标过程...")
        print(f"   任务描述: {task_description}")
        
        # 获取所有待分配的任务
        pending_tasks = self.task_board.get_pending_tasks()
        if not pending_tasks:
            print("   ⚠️ 没有待分配的任务")
            return False
        
        # 通知所有工蜂开始竞标
        for agent in self.registered_agents:
            if hasattr(agent, 'auto_bid_on_tasks'):
                print(f"   📣 通知 {agent.name} 开始任务竞标...")
                try:
                    agent.auto_bid_on_tasks()
                except Exception as e:
                    print(f"   ❌ {agent.name} 竞标失败: {str(e)}")
        
        return True
    
    def _get_task_by_id(self, task_id: str) -> Optional[TaskAnnouncement]:
        """根据任务ID获取任务详情"""
        all_tasks = self.task_board.get_all_tasks()
        for task in all_tasks:
            if task.task_id == task_id:
                return task
        return None
    
    
    def assign_task(self, task_id: str, agent_name: str) -> bool:
        """分配任务给指定Agent"""
        success = self.task_board.assign_task(task_id, agent_name)
        if success:
            # 注意：active_tasks在任务开始执行时才会更新
            self.task_queue.append(task_id)
        return success
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        # 统计IN_PROGRESS状态的任务
        all_tasks = self.task_board.get_all_tasks()
        in_progress_tasks = [task for task in all_tasks if task.task_status == "IN_PROGRESS"]
        
        return {
            "scheduler_name": self.name,
            "total_tasks": len(all_tasks),
            "pending_tasks": len(self.task_board.get_pending_tasks()),
            "active_tasks": len(in_progress_tasks),
            "completed_tasks": len(self.task_board.completed_tasks),
            "task_queue_length": len(self.task_queue),
            "timestamp": datetime.now().isoformat()
        }
    
    def show_bidding_status(self, task_id: str = None):
        """显示竞标状态"""
        if task_id:
            # 显示特定任务的竞标状态
            proposals = self.task_board.get_task_proposals(task_id)
            print(f"\n📊 任务 {task_id} 的竞标状态:")
            if proposals:
                for proposal in proposals:
                    print(f"   📝 {proposal.agent_name}: 置信度={proposal.confidence}, 时间={proposal.estimated_time}")
            else:
                print("   暂无提案")
        else:
            # 显示所有任务的竞标状态
            pending_tasks = self.task_board.get_pending_tasks()
            print(f"\n📊 系统竞标状态 (共 {len(pending_tasks)} 个待分配任务):")
            for task in pending_tasks:
                proposals = self.task_board.get_task_proposals(task.task_id)
                print(f"   📋 {task.task_name} ({task.task_id}): {len(proposals)} 个提案")
                for proposal in proposals:
                    print(f"      📝 {proposal.agent_name}: {proposal.confidence}, {proposal.estimated_time}")
    
    def run_workflow(self, task_description: str, inputs: Dict[str, Any] = None) -> bool:
        """运行完整工作流"""
        if inputs is None:
            inputs = {}
        
        print(f"\n🚀 调度蜂启动工作流...")
        print(f"   任务: {task_description}")
        
        # 发布任务
        success = self.publish_tasks(task_description, inputs)
        if not success:
            print("❌ 工作流启动失败")
            return False
        
        # 通知所有Agent开始执行分配的任务
        print("\n📢 通知所有Agent开始执行分配的任务...")
        for agent in self.registered_agents:
            if hasattr(agent, 'work_on_assigned_tasks'):
                try:
                    agent.work_on_assigned_tasks()
                except Exception as e:
                    print(f"❌ {agent.name} 执行任务失败: {e}")
        
        # 监控任务执行
        print("\n📊 监控任务执行...")
        start_time = time.time()
        
        while True:
            # 检查系统状态
            status = self.get_system_status()
            print(f"   状态: 活跃任务={status['active_tasks']}, 已完成={status['completed_tasks']}")
            
            # 如果所有任务都完成，退出循环
            if status['active_tasks'] == 0 and status['pending_tasks'] == 0:
                print("\n✅ 所有任务已完成！")
                break
            
            # 超时检查
            if time.time() - start_time > 300:  # 5分钟超时
                print("\n⚠️ 工作流执行超时")
                break
            
            time.sleep(5)  # 每5秒检查一次
        
        # 显示最终状态
        final_status = self.get_system_status()
        print(f"\n📊 工作流完成状态:")
        print(f"   总任务数: {final_status['total_tasks']}")
        print(f"   已完成任务: {final_status['completed_tasks']}")
        print(f"   执行时间: {int(time.time() - start_time)} 秒")
        
        return True

# 创建全局实例
task_board = TaskBoard()
task_dag = TaskDAG()
scheduler_bee = SchedulerBee(task_board, task_dag)



# 导入与注册智能工蜂移动到 __main__ 保护块中，避免导入时循环依赖

# 主程序
if __name__ == "__main__":
    print("🚀 启动Bee-MAS智能调度系统...")

    # 运行时再导入并注册工蜂，防止导入时循环
    import sys
    import os
    
    # 添加项目根目录到Python路径，确保能够使用绝对导入
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # 项目根目录
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    try:
        # 尝试使用绝对导入
        from bee_mas.agents.parameter_analysis_bee import ParameterAnalysisBee
        from bee_mas.agents.modeling_bee import ModelingBee
        from bee_mas.agents.assembly_bee import AssemblyBee
    except ImportError as e:
        print("❌ 无法导入工蜂模块，请确保文件结构正确")
        print(f"导入错误详情: {e}")
        print(f"当前Python路径: {sys.path}")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"脚本所在目录: {current_dir}")
        
        # 检查agents目录是否存在
        agents_dir = os.path.join(current_dir, "agents")
        print(f"agents目录是否存在: {os.path.exists(agents_dir)}")
        
        # 检查agents/__init__.py是否存在
        agents_init = os.path.join(agents_dir, "__init__.py")
        print(f"agents/__init__.py是否存在: {os.path.exists(agents_init)}")
        
        # 列出agents目录中的文件
        if os.path.exists(agents_dir):
            print(f"agents目录中的文件: {os.listdir(agents_dir)}")
        
        exit(1)

    # 创建智能工蜂
    工况分析蜂 = ParameterAnalysisBee(task_board)
    三维建模蜂 = ModelingBee(task_board)
    装配蜂 = AssemblyBee(task_board)

    # 注册智能工蜂到调度蜂
    scheduler_bee.register_agent(工况分析蜂)
    scheduler_bee.register_agent(三维建模蜂)
    scheduler_bee.register_agent(装配蜂)

    print("\n" + "="*50)
    print("开始智能工作流程...")
    print("="*50)

    # 运行完整的工作流程
    scheduler_bee.run_workflow("为小型传送带设计一组直齿圆柱齿轮，期望模数2左右，齿数在20~30，常规材料与制造工艺。")

    print("\n🎉 Bee-MAS智能系统运行完成！")