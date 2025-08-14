import autogen
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import time
import json
import requests

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

class LLMClient:
    """LLM API客户端 - 支持多种LLM服务"""
    
    def __init__(self, api_type: str = "deepseek", api_key: str = None, base_url: str = None):
        self.api_type = api_type
        self.api_key = api_key or "sk-1e54707380d7482ab298e7f566f28808"
        self.base_url = base_url or "https://api.deepseek.com/v1"
        
    def generate_response(self, prompt: str, system_message: str = None) -> str:
        """生成LLM响应"""
        try:
            if self.api_type == "deepseek":
                return self._call_deepseek(prompt, system_message)
            else:
                # 模拟LLM响应（用于测试）
                return self._simulate_llm_response(prompt, system_message)
        except Exception as e:
            print(f"⚠️ LLM API调用失败: {e}")
            return self._simulate_llm_response(prompt, system_message)
    
    def _call_deepseek(self, prompt: str, system_message: str = None) -> str:
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        response = requests.post(f"{self.base_url}/chat/completions", 
                               headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
    
    def _simulate_llm_response(self, prompt: str, system_message: str = None) -> str:
        """模拟LLM响应（用于测试）"""
        # 基于提示词的关键词匹配，生成合理的响应
        if "任务分析" in prompt or "分析任务" in prompt:
            return "基于我的专业能力，我能够胜任这个任务。我将采用系统化的方法进行分析，确保结果的准确性和可靠性。"
        elif "执行计划" in prompt or "计划" in prompt:
            return "我的执行计划包括：1) 需求分析 2) 方案设计 3) 实施执行 4) 质量验证。预计需要15-20分钟完成。"
        elif "置信度" in prompt:
            return "基于任务复杂度和我的专业能力，我对完成此任务的置信度为高。"
        else:
            return "我理解任务需求，有信心能够高质量地完成这项工作。"

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
        print(f"💬 {self.name}: {content}")
        return message

class SmartBeeAgent(BeeAgent):
    """智能工蜂 - 集成LLM API的智能工蜂"""
    
    def __init__(self, name: str, capabilities: List[str], task_board: TaskBoard, 
                 llm_client: LLMClient = None):
        super().__init__(name, capabilities, task_board)
        self.llm_client = llm_client or LLMClient()
        self.task_history: List[str] = []  # 任务执行历史
    
    def analyze_task(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """智能分析任务，判断是否适合执行"""
        system_message = f"""你是{self.name}，具备以下专业能力：{', '.join(self.capabilities)}。

你的任务是分析给定的工程任务，判断是否适合由你来执行。

请分析以下方面：
1. 任务与你的专业能力的匹配度
2. 任务的复杂度和风险
3. 你的执行优势
4. 预估完成时间

请以JSON格式返回分析结果，包含：
- "suitable": true/false (是否适合)
- "confidence": "高"/"中"/"低" (执行置信度)
- "reasoning": "分析理由"
- "estimated_time": "预估时间"
- "execution_plan": "执行计划"
- "risks": "潜在风险" """

        prompt = f"""请分析以下任务：

任务名称：{task.task_name}
任务描述：{task.description}
输入参数：{task.inputs}
交付物：{task.deliverable}
截止时间：{task.deadline}

请判断我是否适合执行这个任务，并给出详细分析。"""

        try:
            response = self.llm_client.generate_response(prompt, system_message)
            print(f"   LLM响应: {response[:200]}...")  # 调试信息
            
            # 尝试解析JSON响应
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                
                try:
                    analysis = json.loads(json_str)
                    # 验证必要字段
                    required_fields = ["suitable", "confidence", "execution_plan", "estimated_time"]
                    for field in required_fields:
                        if field not in analysis:
                            print(f"   ⚠️ 缺少字段: {field}")
                            analysis[field] = self._get_default_value(field)
                    
                    return analysis
                except json.JSONDecodeError as e:
                    print(f"   ⚠️ JSON解析失败: {e}")
                    return self._default_task_analysis(task)
            else:
                # 如果无法解析JSON，返回默认分析
                print("   ⚠️ 响应中未找到JSON格式")
                return self._default_task_analysis(task)
        except Exception as e:
            print(f"⚠️ 任务分析失败: {e}")
            return self._default_task_analysis(task)
    
    def _default_task_analysis(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """默认任务分析（当LLM调用失败时使用）"""
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
    
    def _get_default_value(self, field: str) -> Any:
        """获取字段的默认值"""
        defaults = {
            "suitable": True,
            "confidence": "中",
            "reasoning": "基于默认分析",
            "estimated_time": "15分钟",
            "execution_plan": "采用标准流程执行任务",
            "risks": "无明显风险"
        }
        return defaults.get(field, "未知")
    
    def generate_intelligent_proposal(self, task: TaskAnnouncement) -> TaskProposal:
        """生成智能提案"""
        # 分析任务
        analysis = self.analyze_task(task)
        
        if not analysis.get("suitable", False):
            # 如果不适合，不提交提案
            print(f"❌ {self.name} 认为不适合执行任务 {task.task_name}")
            return None
        
        # 安全地获取字段值，确保类型正确
        execution_plan = analysis.get("execution_plan", "采用标准流程执行任务")
        confidence = analysis.get("confidence", "中")
        estimated_time = analysis.get("estimated_time", "15分钟")
        
        # 类型检查和转换
        if isinstance(execution_plan, list):
            execution_plan = " ".join(execution_plan)
        elif not isinstance(execution_plan, str):
            execution_plan = str(execution_plan)
        
        if isinstance(confidence, list):
            confidence = confidence[0] if confidence else "中"
        elif not isinstance(confidence, str):
            confidence = str(confidence)
        
        if isinstance(estimated_time, list):
            estimated_time = estimated_time[0] if estimated_time else "15分钟"
        elif not isinstance(estimated_time, str):
            estimated_time = str(estimated_time)
        
        # 生成提案
        proposal = TaskProposal(
            proposal_id=f"PROP-{str(uuid.uuid4())[:8].upper()}",
            task_id=task.task_id,
            agent_name=self.name,
            role_declaration=f"我是{self.name}，专业从事{', '.join(self.capabilities)}工作",
            execution_plan=execution_plan,
            confidence=confidence,
            estimated_time=estimated_time,
            timestamp=datetime.now().isoformat()
        )
        
        # 提交提案
        if self.task_board.submit_proposal(task.task_id, proposal):
            print(f"✅ {self.name} 已提交智能提案: {proposal.proposal_id}")
            print(f"   置信度: {proposal.confidence}, 预估时间: {proposal.estimated_time}")
            return proposal
        else:
            print(f"❌ 提案提交失败")
            return None
    
    def auto_bid_on_tasks(self):
        """自动竞标适合的任务"""
        available_tasks = self.view_tasks()
        if not available_tasks:
            return
        
        print(f"\n🤖 {self.name} 开始自动任务分析...")
        
        for task in available_tasks:
            if task.task_status == "PENDING" and not task.assigned_agent:
                # 检查是否已经有提案
                existing_proposals = self.task_board.get_task_proposals(task.task_id)
                has_my_proposal = any(p.agent_name == self.name for p in existing_proposals)
                
                print(f"   任务 {task.task_name} 现有提案: {len(existing_proposals)} 个")
                if existing_proposals:
                    for p in existing_proposals:
                        print(f"     - {p.agent_name}: {p.proposal_id}")
                
                if has_my_proposal:
                    print(f"   跳过任务: {task.task_name} (已有我的提案)")
                    continue
                
                print(f"   分析任务: {task.task_name}")
                proposal = self.generate_intelligent_proposal(task)
                if proposal:
                    self.task_history.append(task.task_id)
                    print(f"   ✅ 已提交提案")
                else:
                    print(f"   ❌ 不适合此任务")
    
    def send_intelligent_message(self, content: str, stage: str, message_type: str = "TASK_UPDATE", 
                               receiver: Optional[str] = None, related_task_id: Optional[str] = None):
        """发送智能消息"""
        # 使用LLM优化消息内容
        system_message = f"""你是{self.name}，一个专业的工程Agent。

请优化以下消息内容，使其更加专业、清晰和有用。
保持原有的核心信息，但改进表达方式。"""

        prompt = f"""请优化以下消息内容：

原始消息：{content}
消息类型：{message_type}
阶段：{stage}

请提供优化后的消息内容："""

        try:
            optimized_content = self.llm_client.generate_response(prompt, system_message)
            # 如果LLM优化失败，使用原始内容
            final_content = optimized_content if len(optimized_content) > 10 else content
        except:
            final_content = content
        
        return super().send_message(final_content, stage, message_type, receiver, related_task_id)

class SchedulerBee:
    """调度蜂 - 负责任务分解、分配和协调"""
    
    def __init__(self, task_board: TaskBoard, task_dag: TaskDAG):
        self.task_board = task_board
        self.task_dag = task_dag
        self.agents: Dict[str, SmartBeeAgent] = {}
        self.agent_capabilities = {
            "工况分析蜂": ["参数计算", "需求分析", "工程计算"],
            "三维建模蜂": ["3D建模", "OpenSCAD", "几何设计"],
            "装配蜂": ["装配设计", "空间定位", "干涉检查"],
            "验证蜂": ["设计验证", "质量检查", "可行性分析"]
        }
    
    def register_agent(self, agent: SmartBeeAgent):
        """注册智能工蜂"""
        self.agents[agent.name] = agent
    
    def decompose_task(self, user_request: str) -> List[TaskAnnouncement]:
        """使用思维链方法分解用户请求为子任务"""
        # 简化的任务分解逻辑
        if "齿轮" in user_request:
            tasks = [
                TaskAnnouncement(
                    task_id=f"TASK-{str(uuid.uuid4())[:8].upper()}",
                    task_name="齿轮参数分析",
                    description="分析齿轮设计需求，计算模数、齿数、压力角等关键参数",
                    inputs={"task_type": "齿轮设计", "requirements": user_request},
                    deliverable="齿轮设计参数表",
                    deadline="15 minutes",
                    created_by="调度蜂",
                    task_status="PENDING"
                ),
                TaskAnnouncement(
                    task_id=f"TASK-{str(uuid.uuid4())[:8].upper()}",
                    task_name="齿轮3D建模",
                    description="根据参数生成OpenSCAD脚本，创建齿轮的3D模型",
                    inputs={"task_type": "齿轮建模"},
                    deliverable="齿轮OpenSCAD脚本",
                    deadline="20 minutes",
                    created_by="调度蜂",
                    task_status="PENDING"
                ),
                TaskAnnouncement(
                    task_id=f"TASK-{str(uuid.uuid4())[:8].upper()}",
                    task_name="齿轮装配设计",
                    description="设计齿轮的装配方案和安装说明",
                    inputs={"task_type": "装配设计"},
                    deliverable="装配脚本和说明",
                    deadline="15 minutes",
                    created_by="调度蜂",
                    task_status="PENDING"
                ),
                TaskAnnouncement(
                    task_id=f"TASK-{str(uuid.uuid4())[:8].upper()}",
                    task_name="齿轮设计验证",
                    description="验证齿轮设计的合理性和装配可行性",
                    inputs={"task_type": "设计验证"},
                    deliverable="验证报告",
                    deadline="10 minutes",
                    created_by="调度蜂",
                    task_status="PENDING"
                )
            ]
            
            # 设置依赖关系
            self.task_dag.add_task(tasks[0], [])  # 参数分析无依赖
            self.task_dag.add_task(tasks[1], [tasks[0].task_id])  # 建模依赖参数分析
            self.task_dag.add_task(tasks[2], [tasks[1].task_id])  # 装配依赖建模
            self.task_dag.add_task(tasks[3], [tasks[2].task_id])  # 验证依赖装配
            
            return tasks
        else:
            # 通用任务分解
            return [
                TaskAnnouncement(
                    task_id=f"TASK-{str(uuid.uuid4())[:8].upper()}",
                    task_name="需求分析",
                    description="分析用户需求，确定具体参数",
                    inputs={"requirements": user_request},
                    deliverable="需求分析报告",
                    deadline="20 minutes",
                    created_by="调度蜂",
                    task_status="PENDING"
                )
            ]
    
    def publish_tasks(self, tasks: List[TaskAnnouncement]):
        """发布任务到公告板"""
        for task in tasks:
            self.task_board.post_task(task)
            print(f"✅ 已发布任务: {task.task_name} ({task.task_id})")
    
    def evaluate_proposal(self, proposal: TaskProposal) -> float:
        """评估提案质量，返回评分"""
        score = 0.0
        
        # 基础分：根据置信度
        confidence_scores = {"高": 30, "中": 20, "低": 10}
        score += confidence_scores.get(proposal.confidence, 15)
        
        # 技能匹配分：检查Agent能力是否匹配任务需求
        task = self.task_dag.tasks.get(proposal.task_id)
        if task:
            agent_caps = self.agent_capabilities.get(proposal.agent_name, [])
            if any(cap in task.description for cap in agent_caps):
                score += 25
        
        # 计划详细程度分
        if len(proposal.execution_plan) > 50:
            score += 20
        elif len(proposal.execution_plan) > 20:
            score += 15
        else:
            score += 10
        
        # 时间合理性分
        if "分钟" in proposal.estimated_time:
            score += 15
        elif "小时" in proposal.estimated_time:
            score += 10
        
        return score
    
    def assign_tasks(self):
        """根据提案分配任务"""
        # 获取所有有提案的任务，而不仅仅是"可执行"的任务
        pending_tasks = self.task_board.get_pending_tasks()
        assigned_count = 0
        
        for task in pending_tasks:
            if task.task_status == "ASSIGNED":
                continue  # 跳过已分配的任务
                
            proposals = self.task_board.get_task_proposals(task.task_id)
            if not proposals:
                print(f"⚠️ 任务 {task.task_name} 没有收到提案")
                continue
            
            # 评估所有提案
            scored_proposals = []
            for proposal in proposals:
                score = self.evaluate_proposal(proposal)
                scored_proposals.append((proposal, score))
            
            # 选择得分最高的提案
            if scored_proposals:
                best_proposal, best_score = max(scored_proposals, key=lambda x: x[1])
                
                # 分配任务
                if self.task_board.assign_task(task.task_id, best_proposal.agent_name):
                    print(f"🎯 任务 {task.task_name} 已分配给 {best_proposal.agent_name} (评分: {best_score})")
                    
                    # 更新DAG中的任务状态
                    self.task_dag.tasks[task.task_id].task_status = "ASSIGNED"
                    assigned_count += 1
                else:
                    print(f"❌ 任务 {task.task_name} 分配失败")
            else:
                print(f"⚠️ 任务 {task.task_name} 没有有效提案")
        
        print(f"\n📊 任务分配完成: 成功分配 {assigned_count} 个任务")
    
    def get_system_status(self) -> str:
        """获取系统状态概览"""
        all_tasks = self.task_board.get_all_tasks()
        pending_tasks = self.task_board.get_pending_tasks()
        assigned_tasks = [t for t in all_tasks if t.task_status == "ASSIGNED"]
        ready_tasks = self.task_dag.get_ready_tasks()
        
        status = f"""
=== 调度蜂系统状态 ===
总任务数: {len(self.task_dag.tasks)}
待分配任务: {len(pending_tasks)}
已分配任务: {len(assigned_tasks)}
可执行任务: {len(ready_tasks)}
已完成任务: {len(self.task_board.completed_tasks)}
注册的智能工蜂: {len(self.agents)}

任务依赖关系:
"""
        
        for task_id, deps in self.task_dag.dependencies.items():
            task_name = self.task_dag.tasks[task_id].task_name
            deps_names = []
            for dep_id in deps:
                dep_task = self.task_dag.tasks.get(dep_id)
                if dep_task:
                    deps_names.append(dep_task.task_name)
                else:
                    deps_names.append(f"未知任务({dep_id})")
            status += f"- {task_name} 依赖: {', '.join(deps_names) if deps_names else '无'}\n"
        
        status += "=================="
        return status
    
    def show_bidding_status(self) -> str:
        """显示竞标状态"""
        pending_tasks = self.task_board.get_pending_tasks()
        
        if not pending_tasks:
            return "没有待分配的任务"
        
        status = "\n=== 竞标状态 ===\n"
        
        for task in pending_tasks:
            proposals = self.task_board.get_task_proposals(task.task_id)
            status += f"\n任务: {task.task_name} ({task.task_id})\n"
            status += f"状态: {task.task_status}\n"
            
            if proposals:
                status += f"提案数量: {len(proposals)}\n"
                for i, proposal in enumerate(proposals, 1):
                    status += f"  提案{i}: {proposal.agent_name} "
                    status += f"(置信度: {proposal.confidence}, "
                    status += f"时间: {proposal.estimated_time})\n"
            else:
                status += "提案数量: 0\n"
        
        status += "=================="
        return status
    
    def run_workflow(self, user_request: str):
        """运行完整的工作流程"""
        print(f"\n🚀 开始执行任务: {user_request}")
        
        # 1. 任务分解
        print("\n📋 步骤1: 任务分解")
        tasks = self.decompose_task(user_request)
        print(f"   分解出 {len(tasks)} 个子任务")
        
        # 2. 发布任务
        print("\n📢 步骤2: 发布任务到公告板")
        self.publish_tasks(tasks)
        
        # 3. 智能工蜂自动竞标
        print("\n🤖 步骤3: 智能工蜂自动分析和竞标")
        self.trigger_intelligent_bidding()
        
        # 显示竞标状态
        print("\n📊 竞标状态:")
        print(self.show_bidding_status())
        
        # 4. 分配任务
        print("\n🎯 步骤4: 智能分配任务")
        self.assign_tasks()
        
        # 5. 显示最终状态
        print("\n📊 最终系统状态:")
        final_status = self.get_system_status()
        print(final_status)
    
    def trigger_intelligent_bidding(self):
        """触发智能工蜂的自动竞标"""
        print("   智能工蜂开始分析任务...")
        
        # 获取所有待分配任务
        pending_tasks = self.task_board.get_pending_tasks()
        if not pending_tasks:
            print("   没有待分配的任务")
            return
        
        print(f"   发现 {len(pending_tasks)} 个待分配任务")
        
        for agent_name, agent in self.agents.items():
            print(f"   🤖 {agent_name} 开始任务分析...")
            agent.auto_bid_on_tasks()
            time.sleep(0.5)  # 减少等待时间
        
        print("   智能竞标完成！")
    
    def find_best_agent_for_task(self, task: TaskAnnouncement) -> Optional[SmartBeeAgent]:
        """为任务找到最合适的工蜂"""
        best_agent = None
        best_score = 0
        
        for agent_name, agent in self.agents.items():
            score = 0
            agent_caps = self.agent_capabilities.get(agent_name, [])
            
            # 根据任务描述匹配能力
            for cap in agent_caps:
                if cap in task.description:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent

# 创建全局实例
task_board = TaskBoard()
task_dag = TaskDAG()
scheduler_bee = SchedulerBee(task_board, task_dag)

# 创建LLM客户端
llm_client = LLMClient("deepseek")

# 创建智能工蜂
工况分析蜂 = SmartBeeAgent("工况分析蜂", ["参数计算", "需求分析", "工程计算"], task_board, llm_client)
三维建模蜂 = SmartBeeAgent("三维建模蜂", ["3D建模", "OpenSCAD", "几何设计"], task_board, llm_client)
装配蜂 = SmartBeeAgent("装配蜂", ["装配设计", "空间定位", "干涉检查"], task_board, llm_client)
验证蜂 = SmartBeeAgent("验证蜂", ["设计验证", "质量检查", "可行性分析"], task_board, llm_client)

# 注册智能工蜂到调度蜂
scheduler_bee.register_agent(工况分析蜂)
scheduler_bee.register_agent(三维建模蜂)
scheduler_bee.register_agent(装配蜂)
scheduler_bee.register_agent(验证蜂)

# 主程序
if __name__ == "__main__":
    print("🚀 启动Bee-MAS智能调度系统...")
    
    print("\n" + "="*50)
    print("开始完整智能工作流程...")
    print("="*50)
    
    # 运行完整的工作流程
    scheduler_bee.run_workflow("生成一个齿轮")
    
    print("\n🎉 Bee-MAS智能系统运行完成!")