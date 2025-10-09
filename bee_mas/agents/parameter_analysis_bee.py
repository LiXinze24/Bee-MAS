#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工况分析蜂模块 - 专业的需求分析和参数计算（完全基于 Dify API）
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
import requests
from ..main import SmartBeeAgent, TaskAnnouncement


class ParameterAnalysisBee(SmartBeeAgent):
    """工况分析蜂 - 专业的需求分析和参数计算（使用 Dify API）"""
    
    def __init__(self, task_board, llm_client=None):
        # llm_client 参数保留以兼容基类/调用方，但本类不会使用
        super().__init__(
            name="工况分析蜂",
            capabilities=["参数计算", "需求分析", "工程计算"],
            task_board=task_board
        )
        # Dify 必选配置（通过环境变量）
        self.dify_api_url: Optional[str] = os.getenv("DIFY_PARAMETER_API_URL", os.getenv("DIFY_API_URL"))
        self.dify_api_key: Optional[str] = os.getenv("DIFY_PARAMETER_API_KEY", os.getenv("DIFY_API_KEY"))
        # 可选：应用/工作流ID，不同部署可能字段不同，统称
        self.dify_app_id: Optional[str] = os.getenv("DIFY_PARAMETER_APP_ID") or os.getenv("DIFY_PARAMETER_WORKFLOW_ID")
        # 可选：返回结果路径（点号分隔），默认 data.outputs.result
        self.dify_result_path: str = os.getenv("DIFY_PARAMETER_RESULT_PATH", "data.outputs.result")
    
    def execute_task(self, task_id: str) -> bool:
        """执行参数分析任务（仅 Dify）"""
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
            result = self._execute_parameter_analysis(task)
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
    
    def _execute_parameter_analysis(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """执行参数分析（仅调用 Dify）"""
        if not self._is_dify_configured():
            raise RuntimeError("未配置 Dify 环境变量（DIFY_API_URL, DIFY_API_KEY[,+ DIFY_APP_ID/WORKFLOW_ID 可选]）")
        # 明确提示：非API链接不是API入口
        api_url = self.dify_api_url or ""
        if (
            "/chat/" in api_url or  # 聊天页面链接
            "/workflow/" in api_url and not "/workflows/run" in api_url or  # 工作流页面链接（不是API）
            (not api_url.startswith(("http://api.", "https://api.", "https://", "http://"))) or  # 无效协议
            (".app/" in api_url and not ("/v1/" in api_url or "/api/" in api_url))  # .app域名但没有API路径
        ):
            raise RuntimeError(
                "当前 DIFY_API_URL 看起来不是API端点，而是网页链接。" \
                "请在 Dify 控制台复制工作流/应用的API运行接口（通常形如 /v1/workflows/run 或 /apps/{id}/workflows/run），" \
                "并设置到 DIFY_API_URL。正确的API端点应该包含 '/v1/' 或 '/api/' 路径。"
            )
        result = self._call_dify_parameter_analysis(task)
        if not result:
            raise RuntimeError("Dify 返回为空或格式不符合预期")
        return result

    def _is_dify_configured(self) -> bool:
        return bool(self.dify_api_url and self.dify_api_key)

    def _extract_by_path(self, data: Any, path: str) -> Any:
        cur = data
        for key in path.split('.'):
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                return None
        return cur

    def _call_dify_parameter_analysis(self, task: TaskAnnouncement) -> Optional[Dict[str, Any]]:
        """调用 Dify 完成参数分析。
        - URL: DIFY_API_URL（示例：https://host/v1/workflows/run 或 https://host/apps/{id}/workflows/run）
        - Header: Authorization: Bearer <DIFY_API_KEY>
        - Body: { "inputs": {"requirements":..., "task_type":...}, 可选 "app_id": ... }
        返回：期望为 JSON；结果对象默认在 data.outputs.result，可通过 DIFY_RESULT_PATH 覆盖。
        """
        url = (self.dify_api_url or "").rstrip('/')
        headers = {
            "Authorization": f"Bearer {self.dify_api_key}",
            "Content-Type": "application/json"
        }
        payload: Dict[str, Any] = {
            "inputs": {
                "query": task.description
            },
            "user": "bee-mas-system"  # dify api必需的user参数
        }
        if self.dify_app_id:
            payload["app_id"] = self.dify_app_id
        # 如果是工作流api，可能需要response_mode参数
        if "/workflows/run" in url:
            payload["response_mode"] = "blocking"
        
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        content_type = resp.headers.get("Content-Type", "")
        if resp.status_code != 200:
            snippet = resp.text[:200] if resp.text else ""
            raise RuntimeError(f"Dify API 调用失败: {resp.status_code}, Content-Type={content_type}, 响应片段: {snippet}")
        
        # 解析 JSON，给出更友好的错误提示
        try:
            data = resp.json()
        except Exception:
            snippet = resp.text[:200] if resp.text else ""
            raise RuntimeError(f"Dify API 返回非JSON，Content-Type={content_type}，响应片段: {snippet}")
        
        # 允许多种返回格式：1) 直接是所需结构；2) 位于可配置路径（默认 data.outputs.result）；3) 工作流API格式
        result_json: Optional[Dict[str, Any]] = None
        if isinstance(data, dict) and all(k in data for k in ("parameters", "units", "constraints")):
            result_json = data
        elif isinstance(data, dict) and "data" in data:
            # 工作流API格式，尝试从data中提取结果
            workflow_data = data["data"]
            if isinstance(workflow_data, dict):
                # 尝试多种可能的结果路径
                result_json = self._extract_by_path(workflow_data, "outputs.result") or \
                             self._extract_by_path(workflow_data, "result") or \
                             workflow_data
        else:
            result_json = self._extract_by_path(data, self.dify_result_path)
        
        if not result_json:
            # 回显数据结构，帮助用户调整 DIFY_RESULT_PATH
            def visualize_data_structure(d, indent=0):
                spaces = "  " * indent
                if isinstance(d, dict):
                    items = []
                    for k, v in d.items():
                        if isinstance(v, (dict, list)) and len(str(v)) > 100:
                            items.append(f"{spaces}{k}: {type(v).__name__}(...)")
                        else:
                            items.append(f"{spaces}{k}: {v}")
                    return "\n".join(items)
                elif isinstance(d, list):
                    return f"{spaces}List with {len(d)} items"
                else:
                    return f"{spaces}{d}"
            
            structure_info = visualize_data_structure(data) if isinstance(data, dict) else str(data)
            raise RuntimeError(
                f"未能在返回中找到结果对象，请检查 DIFY_RESULT_PATH（当前: {self.dify_result_path}）。" \
                f"返回keys: {list(data.keys()) if isinstance(data, dict) else type(data)}\n" \
                f"数据结构:\n{structure_info}"
            )
        
        return {
            "task_id": task.task_id,
            "agent_name": self.name,
            "execution_time": datetime.now().isoformat(),
            "result_type": "参数分析报告",
            "parameters": result_json.get("parameters", {}),
            "units": result_json.get("units", {}),
            "constraints": result_json.get("constraints", []),
            "assumptions": result_json.get("assumptions", []),
            "recommendations": result_json.get("recommendations", []),
            "summary": result_json.get("summary", "参数分析完成"),
            "raw_dify_response": data
        }
