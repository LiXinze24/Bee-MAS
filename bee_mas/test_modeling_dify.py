#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小测试：三维建模蜂（基于 Dify API）
使用前请设置环境变量：
- DIFY_API_URL
- DIFY_API_KEY
（可选）DIFY_APP_ID 或 DIFY_WORKFLOW_ID

运行示例：
  python -m bee_mas.test_modeling_dify
"""

import os
import uuid
from datetime import datetime

# 只引入最小依赖，避免包初始化时加载 main 里的运行逻辑
from bee_mas.main import TaskBoard, TaskAnnouncement
from bee_mas.agents.modeling_bee import ModelingBee


def run_test():
    # 读取并校验必要环境变量
    url = os.getenv("DIFY_API_URL")
    key = os.getenv("DIFY_API_KEY")
    if not url or not key:
        print("❌ 未配置 DIFY_API_URL 或 DIFY_API_KEY 环境变量")
        return

    print("📌 使用的 Dify 配置：")
    print(f"   DIFY_API_URL = {url}")
    print(f"   DIFY_API_KEY = {'*' * 6 + key[-4:]}")
    app_id = os.getenv("DIFY_APP_ID") or os.getenv("DIFY_WORKFLOW_ID")
    if app_id:
        print(f"   DIFY_APP_ID/WORKFLOW_ID = {app_id}")

    # 构造最小任务
    task_id = f"TASK-{str(uuid.uuid4())[:8].upper()}"
    task = TaskAnnouncement(
        task_id=task_id,
        task_name="齿轮3D建模",
        description="根据齿轮参数生成3D模型和OpenSCAD代码",
        inputs={
            "task_type": "齿轮建模",
            "parameters": {
                "module": 2,
                "teeth": 25,
                "pressure_angle": 20,
                "width": 10
            },
            "requirements": "为小型传送带设计直齿圆柱齿轮的3D模型"
        },
        deliverable="OpenSCAD代码和3D模型文件",
        deadline="15 minutes",
        created_by="测试脚本",
        task_status="PENDING"
    )

    # 初始化任务板与工蜂
    task_board = TaskBoard()
    task_board.post_task(task)

    bee = ModelingBee(task_board, llm_client=None)

    print("\n🚀 开始最小化3D建模测试…")
    ok = bee.execute_task(task_id)
    if not ok:
        print("❌ 执行失败")
        return

    # 直接从bee获取最后一次执行的结果
    if hasattr(bee, '_last_result'):
        result = bee._last_result
        print("\n✅ 执行成功！")
        print("\n📊 详细3D建模结果：")
        print(f"   执行时间: {result.get('execution_time', 'N/A')}")
        print(f"   结果类型: {result.get('result_type', 'N/A')}")
        print(f"   summary: {result.get('summary', 'N/A')}")
        
        # 显示模型文件信息
        model_file = result.get('model_file', '')
        if model_file:
            print(f"\n📁 模型文件: {model_file}")
            if os.path.exists(model_file):
                print(f"   ✅ 文件存在，大小: {os.path.getsize(model_file)} bytes")
            else:
                print(f"   ⚠️ 文件不存在")
        
        # 显示OpenSCAD代码
        openscad_script = result.get('openscad_script', '')
        if openscad_script:
            print("\n🔧 OpenSCAD代码：")
            print("   " + "=" * 50)
            for line in openscad_script.split('\n'):
                print(f"   {line}")
            print("   " + "=" * 50)
        
        # 显示使用的参数
        parameters_used = result.get('parameters_used', {})
        if parameters_used:
            print("\n⚙️ 使用的建模参数：")
            for param, value in parameters_used.items():
                print(f"   {param}: {value}")
    else:
        print("\n⚠️ 无法获取3D建模结果，请检查任务执行情况。")


if __name__ == "__main__":
    run_test()