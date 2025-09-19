#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小测试：工况分析蜂（基于 Dify API）
使用前请设置环境变量：
- DIFY_API_URL
- DIFY_API_KEY
（可选）DIFY_APP_ID 或 DIFY_WORKFLOW_ID

运行示例：
  python -m bee_mas.test_parameter_analysis_dify
"""

import os
import uuid
from datetime import datetime

# 只引入最小依赖，避免包初始化时加载 main 里的运行逻辑
from bee_mas.main import TaskBoard, TaskAnnouncement
from bee_mas.agents.parameter_analysis_bee import ParameterAnalysisBee


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
        task_name="齿轮参数分析",
        description="分析齿轮设计需求，计算模数、齿数、压力角等关键参数",
        inputs={
            "task_type": "齿轮设计",
            "requirements": "为小型传送带设计一组直齿圆柱齿轮，期望模数2左右，齿数在20~30，常规材料与制造工艺。"
        },
        deliverable="齿轮设计参数表",
        deadline="10 minutes",
        created_by="测试脚本",
        task_status="PENDING"
    )

    # 初始化任务板与工蜂
    task_board = TaskBoard()
    task_board.post_task(task)

    bee = ParameterAnalysisBee(task_board, llm_client=None)

    print("\n🚀 开始最小化Dify参数分析测试…")
    ok = bee.execute_task(task_id)
    if not ok:
        print("❌ 执行失败")
        return

    # 直接从bee获取最后一次执行的结果
    if hasattr(bee, '_last_result'):
        result = bee._last_result
        print("\n✅ 执行成功！")
        print("\n📊 详细参数分析结果：")
        print(f"   执行时间: {result.get('execution_time', 'N/A')}")
        print(f"   结果类型: {result.get('result_type', 'N/A')}")
        print(f"   result: {result}")
        
        # 显示参数
        parameters = result.get('parameters', {})
        if parameters:
            print("\n🔧 计算参数：")
            for param, value in parameters.items():
                print(f"   {param}: {value}")
        
        # 显示单位
        units = result.get('units', {})
        if units:
            print("\n📏 参数单位：")
            for param, unit in units.items():
                print(f"   {param}: {unit}")
        
        # 显示约束条件
        constraints = result.get('constraints', [])
        if constraints:
            print("\n⚠️ 约束条件：")
            for constraint in constraints:
                print(f"   - {constraint}")
        
        # 显示假设条件
        assumptions = result.get('assumptions', [])
        if assumptions:
            print("\n💡 假设条件：")
            for assumption in assumptions:
                print(f"   - {assumption}")
        
        # 显示建议
        recommendations = result.get('recommendations', [])
        if recommendations:
            print("\n🎯 建议：")
            for recommendation in recommendations:
                print(f"   - {recommendation}")
    else:
        print("\n⚠️ 无法获取参数分析结果，请检查任务执行情况。")


if __name__ == "__main__":
    run_test()
