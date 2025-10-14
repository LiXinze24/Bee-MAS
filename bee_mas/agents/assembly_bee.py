#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装配蜂模块 - 专业的装配设计和空间定位（完全基于 Dify API）
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
import requests
from ..main import SmartBeeAgent, TaskAnnouncement


class AssemblyBee(SmartBeeAgent):
    """装配蜂 - 专业的装配设计和空间定位（使用 Dify API）"""
    
    def __init__(self, task_board, llm_client=None):
        # llm_client 参数保留以兼容基类/调用方，但本类不会使用
        super().__init__(
            name="装配蜂",
            capabilities=["装配设计", "空间定位", "干涉检查"],
            task_board=task_board
        )
        # Dify 必选配置（通过环境变量）
        self.dify_api_url: Optional[str] = os.getenv("DIFY_ASSEMBLY_API_URL", os.getenv("DIFY_API_URL"))
        self.dify_api_key: Optional[str] = os.getenv("DIFY_ASSEMBLY_API_KEY", os.getenv("DIFY_API_KEY"))
        # 可选：应用/工作流ID，不同部署可能字段不同，统称
        self.dify_app_id: Optional[str] = os.getenv("DIFY_ASSEMBLY_APP_ID") or os.getenv("DIFY_ASSEMBLY_WORKFLOW_ID")
        # 可选：返回结果路径（点号分隔），默认 data.outputs.result
        self.dify_result_path: str = os.getenv("DIFY_ASSEMBLY_RESULT_PATH", "data.outputs.result")
        self.output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def execute_task(self, task_id: str) -> bool:
        """执行装配设计任务（仅 Dify）"""
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
        
        try:
            # 执行装配设计
            result = self._execute_assembly_design(task)
            
            if result:
                # 更新任务状态为完成
                self.task_board.update_task_status(task_id, "COMPLETED")
                print(f"✅ {self.name} 完成任务: {task.task_name}")
                
                # 保存最后结果
                self._last_result = result
                
                # 清理当前任务
                self.current_task = None
                return True
            else:
                print(f"❌ {self.name} 任务执行失败: {task.task_name}")
                self.task_board.update_task_status(task_id, "FAILED")
                return False
                
        except Exception as e:
            print(f"❌ {self.name} 任务执行异常: {e}")
            self.task_board.update_task_status(task_id, "FAILED")
            self.current_task = None
            return False
    
    def _execute_assembly_design(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """执行装配设计任务（仅调用 Dify）"""
        if not self._is_dify_configured():
            raise RuntimeError("未配置 Dify 环境变量（DIFY_API_URL, DIFY_API_KEY[,+ DIFY_APP_ID/WORKFLOW_ID 可选]）")
        
        # 明确提示：非API链接不是API入口
        api_url = self.dify_api_url or ""
        is_invalid_url = False
        reason = ""
        
        if "/workflow/" in api_url and not "/workflows/run" in api_url:  # 工作流页面链接（不是API）
            is_invalid_url = True
            reason = "包含/workflow/但不是/workflows/run"
        elif not api_url.startswith(("http://api.", "https://api.", "https://", "http://")):  # 无效协议
            is_invalid_url = True
            reason = "无效协议"
        elif ".app/" in api_url and not ("/v1/" in api_url or "/api/" in api_url or "/chat-messages" in api_url):  # .app域名但没有API路径
            is_invalid_url = True
            reason = ".app域名但没有API路径"
        
        if is_invalid_url:
            raise RuntimeError(
                f"当前 DIFY_API_URL 看起来不是API端点，而是网页链接（原因：{reason}）。" \
                "请在 Dify 控制台复制应用的聊天API接口（通常形如 /v1/chat-messages），" \
                "并设置到 DIFY_API_URL。正确的API端点应该包含 '/v1/' 或 '/api/' 路径。"
            )
        
        result = self._call_dify_assembly_design(task)
        if not result:
            raise RuntimeError("Dify 返回为空或格式不符合预期")
        return result
    
    def _is_dify_configured(self) -> bool:
        """检查 Dify 配置是否完整"""
        return bool(self.dify_api_url and self.dify_api_key)
    
    def _get_dependency_results(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """获取依赖任务的输出结果"""
        from ..main import data_flow_logger  # 导入全局日志记录器
        
        dependency_results = {}
        
        # 记录依赖解析开始
        data_flow_logger.logger.info(f"开始解析依赖: {task.task_id} by {self.name}")
        data_flow_logger.logger.debug(f"  任务输入: {task.inputs}")
        
        # 确保task_dag存在
        if not hasattr(self.task_board, 'task_dag'):
            data_flow_logger.logger.warning(f"  task_board没有task_dag属性")
            # 尝试从任务输入中获取依赖信息
            if 'dependencies' in task.inputs:
                dependencies = task.inputs.get('dependencies', [])
                data_flow_logger.logger.debug(f"  从任务输入获取的依赖: {dependencies}")
            else:
                return dependency_results
        else:
            # 获取任务的依赖列表
            dependencies = self.task_board.task_dag.get_dependencies(task.task_id)
            data_flow_logger.logger.debug(f"  从task_dag获取的依赖: {dependencies}")
            
            # 如果没有依赖关系，尝试从任务输入中获取
            if not dependencies and 'dependencies' in task.inputs:
                dependencies = task.inputs.get('dependencies', [])
                data_flow_logger.logger.debug(f"  从任务输入获取的依赖: {dependencies}")
        
        data_flow_logger.logger.debug(f"  最终依赖列表: {dependencies}")
        data_flow_logger.logger.debug(f"  已完成任务: {list(self.task_board.completed_tasks.keys())}")
        
        for dep_id in dependencies:
            data_flow_logger.logger.debug(f"  处理依赖任务: {dep_id}")
            # 查找已完成的任务
            if dep_id in self.task_board.completed_tasks:
                dep_task = self.task_board.completed_tasks[dep_id]
                data_flow_logger.logger.debug(f"  找到已完成任务: {dep_task.task_name}, 分配给: {dep_task.assigned_agent}")
                # 获取工蜂实例
                if hasattr(self.task_board, 'scheduler_bee') and self.task_board.scheduler_bee:
                    data_flow_logger.logger.debug(f"  调度蜂存在，注册的工蜂: {[agent.name for agent in self.task_board.scheduler_bee.registered_agents]}")
                    for agent in self.task_board.scheduler_bee.registered_agents:
                        data_flow_logger.logger.debug(f"  检查工蜂: {agent.name}")
                        if agent.name == dep_task.assigned_agent:
                            data_flow_logger.logger.debug(f"  找到匹配的工蜂: {agent.name}")
                            if hasattr(agent, '_last_result'):
                                data_flow_logger.logger.debug(f"  工蜂有_last_result: {type(agent._last_result)}")
                                dependency_results[dep_id] = {
                                    "task_name": dep_task.task_name,
                                    "agent_name": agent.name,
                                    "result": agent._last_result
                                }
                                data_flow_logger.logger.info(f"  获取依赖任务结果: {dep_task.task_name} -> {agent.name}")
                            else:
                                data_flow_logger.logger.warning(f"  工蜂没有_last_result属性")
                            break
            else:
                data_flow_logger.logger.warning(f"  依赖任务未完成或不存在: {dep_id}")
        
        # 记录依赖解析结果
        data_flow_logger.log_dependency_resolution(task.task_id, dependency_results)
        
        # 如果没有找到依赖任务结果，打印调试信息
        if not dependency_results and dependencies:
            print(f"   ⚠️ 未找到依赖任务的输出结果: {dependencies}")
            print(f"   📋 已完成任务列表: {list(self.task_board.completed_tasks.keys())}")
        
        return dependency_results

    def _build_assembly_requirement(self, task: TaskAnnouncement) -> str:
        """构建装配需求摘要，满足Dify API的字符限制"""
        # 获取任务输入参数
        requirements = task.inputs.get('requirements', '')
        task_type = task.inputs.get('task_type', '')
        parameters = task.inputs.get('parameters', {})
        
        print(f"   📋 构建装配需求:")
        print(f"      需求描述: {requirements}")
        print(f"      任务类型: {task_type}")
        print(f"      输入参数: {parameters}")
        
        # 获取依赖任务的输出结果
        dependency_results = self._get_dependency_results(task)
        print(f"      依赖任务结果: {len(dependency_results)} 个")
        
        # 构建装配需求摘要（限制在256字符以内）
        if task_type:
            summary = f"{task_type}"
        else:
            summary = "装配设计"
        
        # 添加关键参数
        if parameters:
            # 取所有关键参数
            param_str = ", ".join([f"{k}:{v}" for k, v in parameters.items()])
            summary += f"({param_str})"
            print(f"      添加输入参数: {param_str}")
        
        # 添加依赖任务的关键参数
        if dependency_results:
            for dep_id, dep_data in dependency_results.items():
                print(f"      处理依赖任务 {dep_id}: {dep_data['task_name']}")
                result = dep_data.get('result', {})
                # 处理3D建模结果
                if result.get('result_type') == '3D建模结果' and result.get('model_file'):
                    summary += f"[{dep_data['task_name']}: 3D模型]"
                    print(f"      添加3D模型: {dep_data['task_name']}")
                # 处理参数分析结果
                elif 'parameters' in result and result['parameters']:
                    print(f"      找到参数: {len(result['parameters'])} 个")
                    # 取所有关键参数
                    param_list = []
                    for k, v in result['parameters'].items():
                        if isinstance(v, dict) and "value" in v:
                            param_list.append(f"{k}:{v['value']}{v.get('unit', '')}")
                        else:
                            param_list.append(f"{k}:{v}")
                    param_str = ", ".join(param_list)
                    summary += f"[{dep_data['task_name']}: {param_str}]"
                    print(f"      添加依赖参数: {param_str}")
                break  # 只添加第一个依赖任务的关键参数
        
        # 添加简短的需求描述
        if requirements and len(summary) < 200:
            # 截取需求描述的前一部分
            req_summary = requirements[:max(20, 256-len(summary)-10)].replace('\n', ' ')
            summary += f" - {req_summary}"
            print(f"      添加需求描述: {req_summary}")
        
        # 确保摘要不超过256字符
        if len(summary) > 256:
            summary = summary[:253] + "..."
            print(f"      截断摘要: {summary}")
        
        print(f"   📝 最终装配需求: {summary}")
        return summary

    def _call_dify_assembly_design(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """调用 Dify 执行装配设计"""
        from ..main import data_flow_logger  # 导入全局日志记录器
        
        # 构造请求体，参考 parameter_analysis_bee.py
        url = (self.dify_api_url or "").rstrip('/')
        headers = {
            "Authorization": f"Bearer {self.dify_api_key}",
            "Content-Type": "application/json"
        }
        
        # 获取依赖任务的输出结果
        dependency_results = self._get_dependency_results(task)
        
        # 保留原有参数格式
        original_inputs = {
            "requirements": task.inputs.get('requirements', ''),
            "task_type": task.inputs.get('task_type', ''),
            "parameters": task.inputs.get('parameters', {}),
            "query": task.inputs.get('requirements', ''),  # 使用requirements作为query字段
        }
        
        # 添加映射后的assembly_requirement参数
        assembly_requirement = self._build_assembly_requirement(task)
        
        # 构建增强的输入参数，包含依赖任务的输出结果
        enhanced_inputs = {
            "assembly_requirement": assembly_requirement,  # 映射后的参数
            **original_inputs  # 保留原有参数
        }
        
        # 如果有依赖任务的输出结果，添加到参数中
        if dependency_results:
            # 提取关键参数信息，压缩到256个字符以内
            compressed_results = {}
            for dep_id, dep_data in dependency_results.items():
                result = dep_data.get('result', {})
                # 处理3D建模结果
                if result.get('result_type') == '3D建模结果' and result.get('model_file'):
                    compressed_results[dep_id] = {
                        "task_name": dep_data['task_name'],
                        "model_file": result.get('model_file', ''),
                        "summary": result.get('summary', '')
                    }
                # 处理参数分析结果
                elif 'parameters' in result and result['parameters']:
                    # 只保留参数名和值，不保留详细描述
                    compressed_params = {}
                    for name, param in result['parameters'].items():
                        if isinstance(param, dict) and 'value' in param:
                            value = param['value']
                            unit = param.get('unit', '')
                            compressed_params[name] = f"{value}{unit}" if unit else str(value)
                        else:
                            compressed_params[name] = str(param)
                    
                    compressed_results[dep_id] = {
                        "task_name": dep_data['task_name'],
                        "parameters": compressed_params
                    }
            
            # 将压缩后的结果转换为JSON字符串
            dependency_results_str = json.dumps(compressed_results, ensure_ascii=False)
            
            # 如果仍然过长，进一步压缩
            if len(dependency_results_str) > 250:
                # 只保留前几个参数
                for dep_id in list(compressed_results.keys()):
                    if 'parameters' in compressed_results[dep_id]:
                        params = compressed_results[dep_id]['parameters']
                        if len(params) > 3:
                            # 只保留前3个参数
                            compressed_results[dep_id]['parameters'] = dict(list(params.items())[:3])
                
                dependency_results_str = json.dumps(compressed_results, ensure_ascii=False)
                
                # 如果仍然过长，只保留参数数量
                if len(dependency_results_str) > 250:
                    for dep_id in list(compressed_results.keys()):
                        if 'parameters' in compressed_results[dep_id]:
                            param_count = len(compressed_results[dep_id]['parameters'])
                            compressed_results[dep_id] = {
                                "task_name": dep_data['task_name'],
                                "param_count": param_count
                            }
                        elif 'model_file' in compressed_results[dep_id]:
                            compressed_results[dep_id] = {
                                "task_name": dep_data['task_name'],
                                "has_model": True
                            }
                    
                    dependency_results_str = json.dumps(compressed_results, ensure_ascii=False)
            
            enhanced_inputs["dependency_results"] = dependency_results_str
            print(f"   🔗 已添加 {len(dependency_results)} 个依赖任务的输出结果（压缩后长度: {len(dependency_results_str)} 字符）")
        
        payload: Dict[str, Any] = {
            "inputs": enhanced_inputs,
            "query": assembly_requirement,  # 聊天API必需的query参数
            "user": "bee-mas-system"  # dify api必需的user参数
        }
        if self.dify_app_id:
            payload["app_id"] = self.dify_app_id
        # 聊天API不需要response_mode参数
        
        try:
            # 记录API请求
            data_flow_logger.log_api_request(self.name, url, payload)
            
            print(f"   📤 向Dify发送请求: {url}")
            print(f"   📝 装配需求: {assembly_requirement[:100]}...")
            
            response = requests.post(url, json=payload, headers=headers, timeout=180)
            response.raise_for_status()
            data = response.json()
            
            # 记录API响应
            data_flow_logger.log_api_response(self.name, response)
            
            print(f"   📥 收到Dify响应: {data.keys()}")
            
            # 解析 Dify 返回结果
            result = self._parse_dify_response(data, task)
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Dify API 请求失败: {e}")
            data_flow_logger.log_error(self.name, str(e))
            # 尝试获取响应内容
            if hasattr(e, 'response') and e.response is not None:
                print(f"   响应状态码: {e.response.status_code}")
                print(f"   响应内容: {e.response.text}")
                data_flow_logger.log_error(self.name, f"响应状态码: {e.response.status_code}, 响应内容: {e.response.text}")
            raise RuntimeError(f"Dify API 请求失败: {e}")
        except Exception as e:
            print(f"❌ Dify API 调用异常: {e}")
            data_flow_logger.log_error(self.name, str(e))
            raise RuntimeError(f"Dify API 调用异常: {e}")
    
    def _parse_dify_response(self, data: Dict[str, Any], task: TaskAnnouncement) -> Dict[str, Any]:
        """解析 Dify 返回结果"""
        # 优先使用 data.data，其次使用 data.answer
        if "data" in data and isinstance(data["data"], dict):
            dify_result = data["data"]
        elif "answer" in data:
            # 如果 answer 是字符串，尝试解析为 JSON
            try:
                dify_result = json.loads(data["answer"])
            except json.JSONDecodeError:
                dify_result = {"summary": data["answer"]}
        else:
            dify_result = {}
        
        # 构造统一返回格式
        result = {
            "task_id": task.task_id,
            "agent_name": self.name,
            "execution_time": datetime.now().isoformat(),
            "result_type": "装配设计结果",
            "summary": dify_result.get("summary", "装配设计完成"),
            "assembly_script": dify_result.get("assembly_script", ""),
            "assembly_file": dify_result.get("assembly_file", ""),
            "components": dify_result.get("components", []),
            "interference_check": dify_result.get("interference_check", ""),
            "is_fallback": False
        }
        
        # 如果 Dify 返回了文件路径，确保文件存在
        if result["assembly_file"] and not os.path.exists(result["assembly_file"]):
            print(f"⚠️ 装配文件不存在: {result['assembly_file']}")
        
        return result
