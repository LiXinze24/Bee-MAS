#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三维建模蜂模块 - 专业的3D建模和OpenSCAD代码生成（完全基于 Dify API）
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
import requests
from ..main import SmartBeeAgent, TaskAnnouncement


class ModelingBee(SmartBeeAgent):
    """三维建模蜂 - 专业的3D建模和OpenSCAD代码生成（使用 Dify API）"""
    
    def __init__(self, task_board, llm_client=None):
        # llm_client 参数保留以兼容基类/调用方，但本类不会使用
        super().__init__(
            name="三维建模蜂",
            capabilities=["3D建模", "OpenSCAD", "CAD设计"],
            task_board=task_board
        )
        # Dify 必选配置（通过环境变量）
        self.dify_api_url: Optional[str] = os.getenv("DIFY_API_URL")
        self.dify_api_key: Optional[str] = os.getenv("DIFY_API_KEY")
        # 可选：应用/工作流ID，不同部署可能字段不同，统称
        self.dify_app_id: Optional[str] = os.getenv("DIFY_APP_ID") or os.getenv("DIFY_WORKFLOW_ID")
        # 可选：返回结果路径（点号分隔），默认 data.outputs.result
        self.dify_result_path: str = os.getenv("DIFY_RESULT_PATH", "data.outputs.result")
        self.output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def execute_task(self, task_id: str) -> bool:
        """执行3D建模任务（仅 Dify）"""
        if not self.current_task:
            self.current_task = task_id
        
        task = self._get_task_by_id(task_id)
        if not task:
            print(f"❌ {self.name}: 未找到任务 {task_id}")
            return False
        
        print(f"\n🚀 {self.name} 开始执行任务: {task.task_name}")
        print(f"   任务描述: {task.description}")
        print(f"   输入参数: {task.inputs}")
        
        try:
            result = self._execute_3d_modeling(task)
            if result:
                # 保存结果供后续使用
                self._last_result = result
                self.task_board.update_task_status(task_id, "COMPLETED")
                print(f"✅ {self.name} 完成任务: {task.task_name}")
                # 不再调用send_intelligent_message避免重复打印
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
    
    def _execute_3d_modeling(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """执行3D建模任务（仅调用 Dify）"""
        if not self._is_dify_configured():
            raise RuntimeError("未配置 Dify 环境变量（DIFY_API_URL, DIFY_API_KEY[,+ DIFY_APP_ID/WORKFLOW_ID 可选]）")
        
        # 明确提示：非API链接不是API入口
        api_url = self.dify_api_url or ""
        is_invalid_url = False
        reason = ""
        
        if "/chat/" in api_url:  # 聊天页面链接
            is_invalid_url = True
            reason = "包含/chat/"
        elif "/workflow/" in api_url and not "/workflows/run" in api_url:  # 工作流页面链接（不是API）
            is_invalid_url = True
            reason = "包含/workflow/但不是/workflows/run"
        elif not api_url.startswith(("http://api.", "https://api.", "https://", "http://")):  # 无效协议
            is_invalid_url = True
            reason = "无效协议"
        elif ".app/" in api_url and not ("/v1/" in api_url or "/api/" in api_url or "/workflows/run" in api_url):  # .app域名但没有API路径
            is_invalid_url = True
            reason = ".app域名但没有API路径"
        
        if is_invalid_url:
            raise RuntimeError(
                f"当前 DIFY_API_URL 看起来不是API端点，而是网页链接（原因：{reason}）。" \
                "请在 Dify 控制台复制工作流/应用的API运行接口（通常形如 /v1/workflows/run 或 /apps/{id}/workflows/run），" \
                "并设置到 DIFY_API_URL。正确的API端点应该包含 '/v1/' 或 '/api/' 路径。"
            )
        
        result = self._call_dify_3d_modeling(task)
        if not result:
            raise RuntimeError("Dify 返回为空或格式不符合预期")
        return result
    
    def _is_dify_configured(self) -> bool:
        """检查 Dify 配置是否完整"""
        return bool(self.dify_api_url and self.dify_api_key)
    
    def _call_dify_3d_modeling(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """调用 Dify 执行3D建模"""
        # 构造请求体，参考 parameter_analysis_bee.py
        url = (self.dify_api_url or "").rstrip('/')
        headers = {
            "Authorization": f"Bearer {self.dify_api_key}",
            "Content-Type": "application/json"
        }
        payload: Dict[str, Any] = {
            "inputs": {
                "requirements": task.inputs.get('requirements', ''),
                "task_type": task.inputs.get('task_type', ''),
                "parameters": task.inputs.get('parameters', {}),
                "query": task.inputs.get('requirements', ''),  # 使用requirements作为query字段
            },
            "user": "bee-mas-system"  # dify api必需的user参数
        }
        if self.dify_app_id:
            payload["app_id"] = self.dify_app_id
        # 如果是工作流api，可能需要response_mode参数
        if "/workflows/run" in url:
            payload["response_mode"] = "blocking"
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            # 解析 Dify 返回结果
            result = self._parse_dify_response(data, task)
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Dify API 请求失败: {e}")
            raise RuntimeError(f"Dify API 请求失败: {e}")
        except Exception as e:
            print(f"❌ Dify API 调用异常: {e}")
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
            "result_type": "3D建模结果",
            "summary": dify_result.get("summary", "3D建模完成"),
            "model_file": dify_result.get("model_file", ""),
            "openscad_script": dify_result.get("openscad_script", ""),
            "parameters_used": dify_result.get("parameters_used", {}),
            "is_fallback": False
        }
        
        # 如果 Dify 返回了文件路径，确保文件存在
        if result["model_file"] and not os.path.exists(result["model_file"]):
            print(f"⚠️ 模型文件不存在: {result['model_file']}")
        
        return result
