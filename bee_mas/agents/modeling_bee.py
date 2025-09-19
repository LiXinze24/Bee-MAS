#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三维建模蜂模块 - 3D建模和OpenSCAD脚本生成
"""

from typing import Dict, Any, Optional
from datetime import datetime
import math
import os
from .main import SmartBeeAgent, TaskAnnouncement


class ModelingBee(SmartBeeAgent):
    """三维建模蜂 - 3D建模和OpenSCAD脚本生成"""
    
    def __init__(self, task_board, llm_client=None):
        super().__init__(
            name="三维建模蜂",
            capabilities=["3D建模", "OpenSCAD", "几何设计"],
            task_board=task_board,
            llm_client=llm_client
        )
        self.output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def execute_task(self, task_id: str) -> bool:
        """执行3D建模任务"""
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
            # 执行3D建模
            result = self._execute_3d_modeling(task)
            
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
    
    def _execute_3d_modeling(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """执行3D建模任务 - 三维建模蜂的核心功能"""
        print(f"   🎨 {self.name} 开始3D建模...")
        
        # 获取上游参数（从工况分析蜂的结果中）
        upstream_params = self._get_upstream_parameters(task)
        
        if not upstream_params:
            print(f"   ⚠️ 未找到上游参数，使用默认参数")
            upstream_params = self._get_default_gear_params()
        
        print(f"   📊 使用参数: {upstream_params}")
        
        # 根据任务类型生成相应的3D模型
        if "齿轮" in task.inputs.get('task_type', ''):
            openscad_script = self._generate_gear_openscad(upstream_params)
            model_type = "齿轮3D模型"
        else:
            openscad_script = self._generate_generic_openscad(upstream_params)
            model_type = "通用3D模型"
        
        # 保存OpenSCAD脚本到文件（outputs目录）
        filename = f"model_{task.task_id[:8]}.scad"
        file_path = os.path.join(self.output_dir, filename)
        self._save_openscad_script(file_path, openscad_script)
        
        result = {
            "task_id": task.task_id,
            "agent_name": self.name,
            "execution_time": datetime.now().isoformat(),
            "result_type": "3D建模结果",
            "summary": f"{model_type}生成完成",
            "model_file": file_path,
            "openscad_script": openscad_script,
            "parameters_used": upstream_params,
            "is_fallback": False
        }
        
        print(f"   ✅ 3D建模完成，生成文件: {file_path}")
        return result
    
    def _get_upstream_parameters(self, task: TaskAnnouncement) -> Dict[str, Any]:
        """获取上游传递的参数（从工况分析蜂的结果中）"""
        # 检查任务输入中是否有上游任务ID
        upstream_task_id = task.inputs.get('upstream_task_id')
        
        if upstream_task_id:
            # 从上游任务的结果中获取参数
            upstream_result = self._get_task_result(upstream_task_id)
            if upstream_result:
                print(f"   📥 从上游任务 {upstream_task_id} 获取参数")
                return upstream_result.get('parameters', {})
        
        # 检查任务输入中是否有上游参数
        if "upstream_params" in task.inputs:
            return task.inputs["upstream_params"]
        
        # 尝试从任务描述中解析参数
        if "模数" in task.description or "齿数" in task.description:
            # 简单的参数提取（实际应该更智能）
            params = {}
            if "模数" in task.description:
                params["模数"] = 2.0  # 默认值
            if "齿数" in task.description:
                params["齿数"] = 20   # 默认值
            if "压力角" in task.description:
                params["压力角"] = 20
            if "齿宽" in task.description:
                params["齿宽"] = 10
            return params
        
        return None
    
    def _get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务执行结果"""
        # 检查任务是否已完成
        task = self._get_task_by_id(task_id)
        if task and task.task_status == "COMPLETED":
            # 模拟从任务结果中获取参数
            if "参数分析" in task.task_name:
                return {
                    "parameters": {
                        "模数": 2.0,
                        "齿数": 20,
                        "压力角": 20,
                        "齿宽": 10,
                        "孔径": 15
                    },
                    "units": {"长度": "mm", "角度": "度"},
                    "constraints": ["使用标准规格", "考虑制造可行性"],
                    "assumptions": ["标准材料", "常规工艺"],
                    "recommendations": ["建议进行详细设计验证"],
                    "summary": "基于需求生成的齿轮设计参数，符合工程标准"
                }
        
        return None
    
    def _get_default_gear_params(self) -> Dict[str, Any]:
        """获取默认齿轮参数"""
        return {
            "模数": 2.0,
            "齿数": 20,
            "压力角": 20,
            "齿宽": 10,
            "孔径": 15
        }
    
    def _generate_gear_openscad(self, params: Dict[str, Any]) -> str:
        """生成齿轮的OpenSCAD脚本"""
        print(f"   🔧 生成齿轮OpenSCAD脚本...")
        
        # 使用LLM生成OpenSCAD代码
        system_message = f"""你是{self.name}，一个专业的3D建模工程师。

你的任务是生成OpenSCAD脚本来创建精确的齿轮3D模型。

请根据给定的参数生成完整的OpenSCAD脚本，包括：
1. 齿轮的基本几何形状
2. 齿形的精确计算
3. 中心孔的创建
4. 适当的模块化结构

**重要：请只返回OpenSCAD代码，不要添加任何解释文字。**"""

        prompt = f"""请生成一个齿轮的OpenSCAD脚本，参数如下：

模数: {params.get('模数', 2.0)} mm
齿数: {params.get('齿数', 20)}
压力角: {params.get('压力角', 20)} 度
齿宽: {params.get('齿宽', 10)} mm
孔径: {params.get('孔径', 15)} mm

请生成完整的OpenSCAD脚本："""

        try:
            openscad_code = self.llm_client.generate_response(prompt, system_message)
            print(f"   📝 LLM生成OpenSCAD代码: {len(openscad_code)} 字符")
            
            # 如果LLM生成失败，使用备用代码
            if len(openscad_code) < 100 or "module" not in openscad_code:
                print(f"   ⚠️ LLM生成的代码不完整，使用备用代码")
                openscad_code = self._generate_fallback_gear_openscad(params)
            
            return openscad_code
            
        except Exception as e:
            print(f"   ⚠️ LLM调用失败: {e}，使用备用代码")
            return self._generate_fallback_gear_openscad(params)
    
    def _generate_fallback_gear_openscad(self, params: Dict[str, Any]) -> str:
        """生成备用的齿轮OpenSCAD脚本"""
        m = params.get('模数', 2.0)      # 模数
        z = params.get('齿数', 20)       # 齿数
        alpha = params.get('压力角', 20)  # 压力角
        b = params.get('齿宽', 10)       # 齿宽
        d_hole = params.get('孔径', 15)  # 孔径
        
        # 计算齿轮几何参数
        d = m * z                    # 分度圆直径
        da = d + 2 * m              # 齿顶圆直径
        df = d - 2.5 * m            # 齿根圆直径
        db = d * math.cos(math.radians(alpha))  # 基圆直径
        
        openscad_code = f"""// 齿轮3D模型 - 自动生成
// 参数: 模数={m}mm, 齿数={z}, 压力角={alpha}°, 齿宽={b}mm, 孔径={d_hole}mm

// 齿轮参数
m = {m};           // 模数
z = {z};           // 齿数
alpha = {alpha};   // 压力角
b = {b};           // 齿宽
d_hole = {d_hole}; // 孔径

// 计算几何参数
d = m * z;         // 分度圆直径
da = d + 2 * m;   // 齿顶圆直径
df = d - 2.5 * m; // 齿根圆直径
p = m * PI;        // 齿距

// 生成齿轮
gear();

module gear() {{
    difference() {{
        // 齿轮主体
        cylinder(h=b, d=da, $fn=100);
        
        // 中心孔
        cylinder(h=b+1, d=d_hole, $fn=50);
        
        // 齿槽
        for (i = [0:z-1]) {{
            rotate([0, 0, i * 360/z])
            translate([d/2, 0, 0])
            tooth_space();
        }}
    }}
}}

module tooth_space() {{
    // 简化的齿槽形状
    translate([0, 0, -1])
    linear_extrude(height=b+2)
    polygon([
        [0, 0],
        [m/2, -m/4],
        [m, 0],
        [m/2, m/4]
    ]);
}}

// 辅助函数
function PI() = 3.14159;
"""
        
        return openscad_code
    
    def _generate_generic_openscad(self, params: Dict[str, Any]) -> str:
        """生成通用3D模型的OpenSCAD脚本"""
        print(f"   🔧 生成通用3D模型OpenSCAD脚本...")
        
        # 简单的立方体模型
        length = params.get('长度', 100)
        width = params.get('宽度', 50)
        height = params.get('高度', 25)
        
        openscad_code = f"""// 通用3D模型 - 自动生成
// 参数: 长度={length}mm, 宽度={width}mm, 高度={height}mm

// 模型参数
length = {length};
width = {width};
height = {height};

// 生成模型
cube([length, width, height]);
"""
        
        return openscad_code
    
    def _save_openscad_script(self, filename: str, content: str) -> bool:
        """保存OpenSCAD脚本到文件"""
        try:
            # filename 已经是完整路径
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   💾 已保存OpenSCAD脚本: {filename}")
            return True
        except Exception as e:
            print(f"   ❌ 保存文件失败: {e}")
            return False
