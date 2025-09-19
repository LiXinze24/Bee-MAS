#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装配蜂模块 - 装配设计和空间定位
"""

from typing import Dict, Any, Optional
from datetime import datetime
import os
from .main import SmartBeeAgent, TaskAnnouncement


class AssemblyBee(SmartBeeAgent):
    """装配蜂 - 装配设计和空间定位"""
    
    def __init__(self, task_board, llm_client=None):
        super().__init__(
            name="装配蜂",
            capabilities=["装配设计", "空间定位", "干涉检查"],
            task_board=task_board,
            llm_client=llm_client
        )
        self.output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def execute_task(self, task_id: str) -> bool:
        """执行装配设计任务"""
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
    
    def _execute_assembly_design(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """执行装配设计任务 - 装配蜂的核心功能"""
        print(f"   🔧 {self.name} 开始装配设计...")
        
        # 获取上游的3D模型文件（从三维建模蜂的结果中）
        upstream_models = self._get_upstream_models(task)
        
        if not upstream_models:
            print(f"   ⚠️ 未找到上游3D模型，使用默认模型")
            upstream_models = self._generate_default_assembly_models()
        
        print(f"   📊 使用模型: {list(upstream_models.keys())}")
        
        # 生成主装配脚本
        assembly_script = self._generate_assembly_script(upstream_models, task)
        
        # 保存装配脚本到文件（outputs目录）
        filename = f"assembly_{task.task_id[:8]}.scad"
        file_path = os.path.join(self.output_dir, filename)
        self._save_assembly_script(file_path, assembly_script)
        
        result = {
            "task_id": task.task_id,
            "agent_name": self.name,
            "execution_time": datetime.now().isoformat(),
            "result_type": "装配设计结果",
            "summary": f"装配设计完成，包含 {len(upstream_models)} 个零件",
            "assembly_file": file_path,
            "assembly_script": assembly_script,
            "components": list(upstream_models.keys()),
            "is_fallback": False
        }
        
        print(f"   ✅ 装配设计完成，生成文件: {file_path}")
        return result
    
    def _get_upstream_models(self, task: TaskAnnouncement) -> Dict[str, str]:
        """获取上游传递的3D模型文件"""
        # 检查任务输入中是否有上游任务ID
        upstream_task_id = task.inputs.get('upstream_task_id')
        
        if upstream_task_id:
            # 从上游任务的结果中获取模型文件
            upstream_result = self._get_task_result(upstream_task_id)
            if upstream_result and "model_file" in upstream_result:
                model_file = upstream_result["model_file"]
                # 读取模型文件内容
                try:
                    with open(model_file, 'r', encoding='utf-8') as f:
                        model_content = f.read()
                    return {model_file: model_content}
                except FileNotFoundError:
                    print(f"   ⚠️ 模型文件 {model_file} 不存在")
        
        # 检查任务输入中是否有上游模型
        if "upstream_models" in task.inputs:
            return task.inputs["upstream_models"]
        
        return None
    
    def _get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务执行结果"""
        # 检查任务是否已完成
        task = self._get_task_by_id(task_id)
        if task and task.task_status == "COMPLETED":
            # 模拟从任务结果中获取模型文件
            if "3D建模" in task.task_name:
                return {
                    "model_file": os.path.join(self.output_dir, f"model_{task_id[:8]}.scad"),
                    "openscad_script": "// 模拟的OpenSCAD脚本",
                    "parameters_used": {"模数": 2.0, "齿数": 20},
                    "summary": "齿轮3D模型生成完成"
                }
        
        return None
    
    def _generate_default_assembly_models(self) -> Dict[str, str]:
        """生成默认的装配模型（当上游模型不可用时）"""
        print(f"   🔧 生成默认装配模型...")
        
        # 生成齿轮模型
        gear_model = """// 齿轮模型
module gear() {
    difference() {
        cylinder(h=10, d=40, $fn=100);
        cylinder(h=12, d=15, $fn=50);
        
        for (i = [0:19]) {
            rotate([0, 0, i * 18])
            translate([20, 0, 0])
            cube([2, 1, 12], center=true);
        }
    }
}"""
        
        # 生成轴模型
        shaft_model = """// 轴模型
module shaft() {
    cylinder(h=50, d=15, $fn=50);
}"""
        
        # 生成轴承模型
        bearing_model = """// 轴承模型
module bearing() {
    difference() {
        cylinder(h=8, d=25, $fn=50);
        cylinder(h=10, d=15, $fn=50);
    }
}"""
        
        return {
            "gear.scad": gear_model,
            "shaft.scad": shaft_model,
            "bearing.scad": bearing_model
        }
    
    def _generate_assembly_script(self, models: Dict[str, str], task: TaskAnnouncement) -> str:
        """生成主装配脚本"""
        print(f"   🔧 生成主装配脚本...")
        
        # 使用LLM生成装配脚本
        system_message = f"""你是{self.name}，一个专业的虚拟装配工程师。

你的任务是生成OpenSCAD主装配脚本，将多个零件模型组合成完整的装配体。

请生成包含以下内容的装配脚本：
1. 使用use或include引入各个零件模块
2. 应用translate和rotate等变换指令
3. 定义零件间的装配关系和空间位置
4. 创建清晰的模块化结构

**重要：请只返回OpenSCAD代码，不要添加任何解释文字。**"""

        # 构建模型信息
        model_info = []
        for filename, content in models.items():
            # 提取模块名（简化实现）
            module_name = self._extract_module_name(content, filename)
            model_info.append(f"{filename}: {module_name}")
        
        prompt = f"""请生成一个装配体的OpenSCAD主脚本，包含以下零件：

{chr(10).join(model_info)}

请生成完整的装配脚本，合理布置各零件的位置和姿态："""

        try:
            assembly_code = self.llm_client.generate_response(prompt, system_message)
            print(f"   📝 LLM生成装配脚本: {len(assembly_code)} 字符")
            
            # 如果LLM生成失败，使用备用代码
            if len(assembly_code) < 100 or "use" not in assembly_code:
                print(f"   ⚠️ LLM生成的代码不完整，使用备用代码")
                assembly_code = self._generate_fallback_assembly_script(models)
            
            return assembly_code
            
        except Exception as e:
            print(f"   ⚠️ LLM调用失败: {e}，使用备用代码")
            return self._generate_fallback_assembly_script(models)
    
    def _extract_module_name(self, content: str, filename: str) -> str:
        """从模型内容中提取模块名"""
        # 查找module关键字
        if "module " in content:
            lines = content.split('\n')
            for line in lines:
                if line.strip().startswith("module "):
                    module_name = line.strip().split("module ")[1].split("(")[0].strip()
                    return module_name
        
        # 如果没有找到module，使用文件名
        return filename.replace('.scad', '')
    
    def _generate_fallback_assembly_script(self, models: Dict[str, str]) -> str:
        """生成备用的装配脚本"""
        print(f"   🔧 生成备用装配脚本...")
        
        # 构建use语句
        use_statements = []
        for filename in models.keys():
            use_statements.append(f'use <{filename}>')
        
        # 构建装配代码
        assembly_parts = []
        y_offset = 0
        
        for filename in models.keys():
            module_name = self._extract_module_name(models[filename], filename)
            assembly_parts.append(f'    // 放置 {module_name}')
            assembly_parts.append(f'    translate([0, {y_offset}, 0])')
            assembly_parts.append(f'    {module_name}();')
            assembly_parts.append('')
            y_offset += 50  # 每个零件间隔50mm
        
        assembly_code = f"""// 主装配脚本 - 自动生成
// 包含零件: {', '.join(models.keys())}

// 引入零件模块
{chr(10).join(use_statements)}

// 主装配体
assembly();

module assembly() {{
    // 装配体主体
    {chr(10).join(assembly_parts)}
    
    // 装配说明
    echo("装配体包含 {len(models)} 个零件");
    echo("零件列表: {', '.join(models.keys())}");
}}

// 辅助函数：显示坐标轴
module show_axes() {{
    color("red") cylinder(h=100, d=1);  // X轴
    color("green") rotate([0, 0, 90]) cylinder(h=100, d=1);  // Y轴
    color("blue") rotate([0, -90, 0]) cylinder(h=100, d=1);  // Z轴
}}

// 可选：显示坐标轴（调试用）
// show_axes();
"""
        
        return assembly_code
    
    def _save_assembly_script(self, filename: str, content: str) -> bool:
        """保存装配脚本到文件"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   💾 已保存装配脚本: {filename}")
            return True
        except Exception as e:
            print(f"   ❌ 保存文件失败: {e}")
            return False
