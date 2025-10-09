#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装配蜂模块 - 装配设计和空间定位（仅 Dify）
"""

from typing import Dict, Any, Optional
from datetime import datetime
import os
import requests
from ..main import SmartBeeAgent, TaskAnnouncement


class AssemblyBee(SmartBeeAgent):
    """装配蜂 - 装配设计和空间定位（仅 Dify）"""
    
    def __init__(self, task_board, llm_client=None):
        super().__init__(
            name="装配蜂",
            capabilities=["装配设计", "空间定位", "干涉检查"],
            task_board=task_board
        )
        self.output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Dify API 配置
        self.dify_api_url = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1")
        self.dify_api_key = os.getenv("DIFY_API_KEY", "")
        self.dify_app_id = os.getenv("DIFY_ASSEMBLY_APP_ID", "")
        self.dify_result_path = os.getenv("DIFY_RESULT_PATH", "outputs")
    
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
        print(f"   🔧 {self.name} 开始装配设计...")
        
        # 检查 Dify 配置
        if not self._is_dify_configured():
            print(f"   ❌ Dify 配置不完整")
            return None
        
        # 检查 API URL 有效性
        if not self.dify_api_url.startswith('http'):
            print(f"   ❌ Dify API URL 无效: {self.dify_api_url}")
            return None
        
        # 调用 Dify API
        result = self._call_dify_assembly_design(task)
        
        if result:
            print(f"   ✅ 装配设计完成")
            return result
        else:
            print(f"   ❌ 装配设计失败")
            return None
    
    def _is_dify_configured(self) -> bool:
        """检查 Dify 配置是否完整"""
        return bool(self.dify_api_key and self.dify_app_id)
    
    def _call_dify_assembly_design(self, task: TaskAnnouncement) -> Optional[Dict[str, Any]]:
        """调用 Dify API 进行装配设计"""
        try:
            # 构造请求体
            inputs = {
                "task_id": task.task_id,
                "task_name": task.task_name,
                "description": task.description,
                "inputs": task.inputs
            }
            
            request_body = {
                "inputs": inputs,
                "response_mode": "blocking",
                "user": "assembly_bee"
            }
            
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {self.dify_api_key}",
                "Content-Type": "application/json"
            }
            
            # 发送请求
            url = f"{self.dify_api_url}/completion-messages"
            response = requests.post(url, json=request_body, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return self._parse_dify_response(response.json(), task)
            else:
                print(f"   ❌ Dify API 调用失败: {response.status_code}")
                print(f"   ❌ 错误信息: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Dify API 调用异常: {e}")
            return None
    
    def _parse_dify_response(self, response_data: Dict[str, Any], task: TaskAnnouncement) -> Dict[str, Any]:
        """解析 Dify 响应结果"""
        try:
            # 从响应中提取结果
            answer = response_data.get("answer", "")
            data = response_data.get("data", {})
            
            # 构造统一格式的输出
            result = {
                "task_id": task.task_id,
                "agent_name": self.name,
                "execution_time": datetime.now().isoformat(),
                "result_type": "装配设计结果",
                "summary": answer or "装配设计完成",
                "assembly_script": answer,
                "components": [],
                "is_fallback": False,
                "dify_response": response_data
            }
            
            return result
            
        except Exception as e:
            print(f"   ❌ 解析 Dify 响应失败: {e}")
