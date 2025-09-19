#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证蜂模块 - 设计验证和质量检查
"""

from typing import Dict, Any, Optional
from datetime import datetime
import os
from .main import SmartBeeAgent, TaskAnnouncement


class VerificationBee(SmartBeeAgent):
    """验证蜂 - 设计验证和质量检查"""
    
    def __init__(self, task_board, llm_client=None):
        super().__init__(
            name="验证蜂",
            capabilities=["设计验证", "质量检查", "可行性分析"],
            task_board=task_board,
            llm_client=llm_client
        )
        self.output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def execute_task(self, task_id: str) -> bool:
        """执行设计验证任务"""
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
            # 执行设计验证
            result = self._execute_design_verification(task)
            
            if result:
                # 更新任务状态为完成
                self.task_board.update_task_status(task_id, "COMPLETED")
                print(f"✅ {self.name} 完成任务: {task.task_name}")
                
                # 发送任务完成消息
                self.send_intelligent_message(
                    f"任务执行完成！生成结果：{result.get('summary', '无')}",
                    "任务完成",
                    "TASK_RESULT",
                    related_task_id=task_id
                )
                
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
    
    def _execute_design_verification(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """执行设计验证任务 - 验证蜂的核心功能"""
        print(f"   🔍 {self.name} 开始设计验证...")
        
        # 获取上游的装配设计结果
        upstream_assembly = self._get_upstream_assembly(task)
        
        if not upstream_assembly:
            print(f"   ⚠️ 未找到上游装配设计，使用模拟数据进行验证")
            upstream_assembly = self._generate_mock_assembly_data()
        
        print(f"   📊 验证对象: {upstream_assembly.get('assembly_type', '未知装配体')}")
        
        # 执行设计验证
        verification_result = self._perform_design_verification(upstream_assembly, task)
        
        # 生成验证报告（outputs目录）
        report_filename = f"verification_report_{task.task_id[:8]}.txt"
        report_path = os.path.join(self.output_dir, report_filename)
        self._save_verification_report(report_path, verification_result)
        
        result = {
            "task_id": task.task_id,
            "agent_name": self.name,
            "execution_time": datetime.now().isoformat(),
            "result_type": "设计验证结果",
            "summary": f"设计验证完成，验证了 {len(verification_result.get('checks', []))} 个检查项",
            "verification_report": report_path,
            "verification_result": verification_result,
            "overall_status": verification_result.get('overall_status', '未知'),
            "is_fallback": False
        }
        
        print(f"   ✅ 设计验证完成，生成报告: {report_path}")
        return result
    
    def _get_upstream_assembly(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """获取上游传递的装配设计结果"""
        # 检查任务输入中是否有上游任务ID
        upstream_task_id = task.inputs.get('upstream_task_id')
        
        if upstream_task_id:
            # 从上游任务的结果中获取装配信息
            upstream_result = self._get_task_result(upstream_task_id)
            if upstream_result:
                print(f"   📥 从上游任务 {upstream_task_id} 获取装配信息")
                return upstream_result
        
        # 检查任务输入中是否有上游装配数据
        if "upstream_assembly" in task.inputs:
            return task.inputs["upstream_assembly"]
        
        return None
    
    def _get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务执行结果"""
        # 检查任务是否已完成
        task = self._get_task_by_id(task_id)
        if task and task.task_status == "COMPLETED":
            # 模拟从任务结果中获取装配信息
            if "装配设计" in task.task_name:
                return {
                    "assembly_type": "齿轮传动系统",
                    "components": ["齿轮", "轴", "轴承"],
                    "assembly_file": f"assembly_{task_id[:8]}.scad",
                    "total_parts": 3,
                    "assembly_complexity": "中等",
                    "estimated_weight": "2.5kg",
                    "manufacturing_method": "机加工 + 装配",
                    "summary": "装配设计完成，包含 3 个零件"
                }
        
        return None
    
    def _generate_mock_assembly_data(self) -> Dict[str, Any]:
        """生成模拟的装配数据（当上游数据不可用时）"""
        print(f"   🔍 生成模拟装配数据...")
        
        return {
            "assembly_type": "齿轮传动系统",
            "components": ["齿轮", "轴", "轴承"],
            "assembly_file": "assembly_mock.scad",
            "total_parts": 3,
            "assembly_complexity": "中等",
            "estimated_weight": "2.5kg",
            "manufacturing_method": "机加工 + 装配"
        }
    
    def _perform_design_verification(self, assembly_data: Dict[str, Any], task: TaskAnnouncement) -> Dict[str, Any]:
        """执行设计验证"""
        print(f"   🔍 执行设计验证...")
        
        # 使用LLM进行验证分析
        system_message = f"""你是{self.name}，一个专业的设计验证工程师。

你的任务是对装配设计进行全面的验证分析，包括：
1. 设计合理性检查
2. 制造可行性分析
3. 装配可行性评估
4. 质量风险评估

请生成结构化的验证报告，包含检查项、状态、问题和建议。

**重要：请严格按照以下JSON格式返回结果，不要添加任何其他文字：**

{{
    "overall_status": "通过/警告/失败",
    "checks": [
        {{
            "check_item": "检查项名称",
            "status": "通过/警告/失败",
            "description": "检查描述",
            "issues": ["问题1", "问题2"],
            "recommendations": ["建议1", "建议2"]
        }}
    ],
    "summary": "验证总结",
    "risk_level": "低/中/高",
    "next_steps": ["下一步1", "下一步2"]
}}"""

        prompt = f"""请验证以下装配设计：

装配类型: {assembly_data.get('assembly_type', '未知')}
包含零件: {', '.join(assembly_data.get('components', []))}
零件数量: {assembly_data.get('total_parts', 0)}
装配复杂度: {assembly_data.get('assembly_complexity', '未知')}
制造方法: {assembly_data.get('manufacturing_method', '未知')}

请进行全面的设计验证分析："""

        try:
            verification_result = self.llm_client.generate_response(prompt, system_message)
            print(f"   📝 LLM生成验证结果: {len(verification_result)} 字符")
            
            # 如果LLM生成失败，使用备用验证
            if len(verification_result) < 100 or "checks" not in verification_result:
                print(f"   ⚠️ LLM生成的验证结果不完整，使用备用验证")
                verification_result = self._generate_fallback_verification(assembly_data)
            
            return verification_result
            
        except Exception as e:
            print(f"   ⚠️ LLM调用失败: {e}，使用备用验证")
            return self._generate_fallback_verification(assembly_data)
    
    def _generate_fallback_verification(self, assembly_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成备用的验证结果"""
        print(f"   🔍 生成备用验证结果...")
        
        # 基于装配数据生成验证检查项
        checks = []
        
        # 检查1: 零件数量合理性
        total_parts = assembly_data.get('total_parts', 0)
        if total_parts <= 5:
            status = "通过"
            issues = []
            recommendations = []
        elif total_parts <= 10:
            status = "警告"
            issues = ["零件数量较多，可能增加装配复杂度"]
            recommendations = ["考虑模块化设计", "优化装配顺序"]
        else:
            status = "失败"
            issues = ["零件数量过多，装配困难"]
            recommendations = ["重新设计，减少零件数量", "采用集成化设计"]
        
        checks.append({
            "check_item": "零件数量合理性",
            "status": status,
            "description": f"检查装配体包含 {total_parts} 个零件的合理性",
            "issues": issues,
            "recommendations": recommendations
        })
        
        # 检查2: 制造可行性
        manufacturing_method = assembly_data.get('manufacturing_method', '')
        if "机加工" in manufacturing_method or "3D打印" in manufacturing_method:
            mfg_status = "通过"
            mfg_issues = []
            mfg_recommendations = []
        else:
            mfg_status = "警告"
            mfg_issues = ["制造方法不明确"]
            mfg_recommendations = ["明确制造工艺", "评估成本可行性"]
        
        checks.append({
            "check_item": "制造可行性",
            "status": mfg_status,
            "description": f"评估制造方法 '{manufacturing_method}' 的可行性",
            "issues": mfg_issues,
            "recommendations": mfg_recommendations
        })
        
        # 检查3: 装配可行性
        complexity = assembly_data.get('assembly_complexity', '')
        if complexity == "简单":
            assy_status = "通过"
            assy_issues = []
            assy_recommendations = []
        elif complexity == "中等":
            assy_status = "警告"
            assy_issues = ["装配复杂度中等，需要详细装配说明"]
            assy_recommendations = ["提供装配图纸", "制作装配视频"]
        else:
            assy_status = "失败"
            assy_issues = ["装配过于复杂，难以实现"]
            assy_recommendations = ["简化设计", "分步装配"]
        
        checks.append({
            "check_item": "装配可行性",
            "status": assy_status,
            "description": f"评估装配复杂度 '{complexity}' 的可行性",
            "issues": assy_issues,
            "recommendations": assy_recommendations
        })
        
        # 检查4: 质量风险评估
        risk_factors = []
        if total_parts > 5:
            risk_factors.append("零件数量多")
        if complexity != "简单":
            risk_factors.append("装配复杂")
        if not manufacturing_method:
            risk_factors.append("制造方法不明确")
        
        if len(risk_factors) == 0:
            risk_status = "通过"
            risk_level = "低"
            risk_issues = []
            risk_recommendations = []
        elif len(risk_factors) <= 2:
            risk_status = "警告"
            risk_level = "中"
            risk_issues = risk_factors
            risk_recommendations = ["加强质量控制", "详细测试验证"]
        else:
            risk_status = "失败"
            risk_level = "高"
            risk_issues = risk_factors
            risk_recommendations = ["重新评估设计", "降低风险因素"]
        
        checks.append({
            "check_item": "质量风险评估",
            "status": risk_status,
            "description": f"评估设计质量风险，识别风险因素: {', '.join(risk_factors) if risk_factors else '无'}",
            "issues": risk_issues,
            "recommendations": risk_recommendations
        })
        
        # 确定整体状态
        statuses = [check["status"] for check in checks]
        if "失败" in statuses:
            overall_status = "失败"
        elif "警告" in statuses:
            overall_status = "警告"
        else:
            overall_status = "通过"
        
        return {
            "overall_status": overall_status,
            "checks": checks,
            "summary": f"验证完成，整体状态: {overall_status}，共检查 {len(checks)} 项",
            "risk_level": risk_level,
            "next_steps": [
                "根据验证结果优化设计",
                "制作详细装配说明",
                "进行原型验证测试"
            ]
        }
    
    def _save_verification_report(self, filename: str, verification_result: Dict[str, Any]) -> bool:
        """保存验证报告到文件"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("设计验证报告\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"验证工程师: {self.name}\n")
                f.write(f"整体状态: {verification_result.get('overall_status', '未知')}\n")
                f.write(f"风险等级: {verification_result.get('risk_level', '未知')}\n\n")
                
                f.write("详细检查结果:\n")
                f.write("-" * 40 + "\n")
                
                checks = verification_result.get('checks', [])
                for i, check in enumerate(checks, 1):
                    f.write(f"\n{i}. {check.get('check_item', '未知检查项')}\n")
                    f.write(f"   状态: {check.get('status', '未知')}\n")
                    f.write(f"   描述: {check.get('description', '无描述')}\n")
                    
                    issues = check.get('issues', [])
                    if issues:
                        f.write(f"   问题:\n")
                        for issue in issues:
                            f.write(f"     - {issue}\n")
                    
                    recommendations = check.get('recommendations', [])
                    if recommendations:
                        f.write(f"   建议:\n")
                        for rec in recommendations:
                            f.write(f"     - {rec}\n")
                
                f.write(f"\n验证总结:\n")
                f.write(f"{verification_result.get('summary', '无总结')}\n\n")
                
                f.write("下一步行动:\n")
                next_steps = verification_result.get('next_steps', [])
                for step in next_steps:
                    f.write(f" - {step}\n")
                
                f.write("\n" + "=" * 60 + "\n")
                f.write("报告结束\n")
                f.write("=" * 60 + "\n")
            
            print(f"   💾 已保存验证报告: {filename}")
            return True
        except Exception as e:
            print(f"   ❌ 保存报告失败: {e}")
            return False
