
# IGD Framework Implementation

实现语义驱动的端到端智能机械设计

## 🐝 系统概述

 IGD (Intelligent Generative Design) 框架的工程实现，这是一个基于语义驱动的统一生成式设计框架。系统采用受蚁群启发的 ACBAC (Ant-Colony Bionic Agent Collaboration) 多智能体协作机制，实现了从自然语言需求到复杂机械产品设计、建模与装配的全流程自动化。

通过集成通用大模型 (LLM)、监督微调模型 (SFT LLM) 以及特定的任务神经网络 (TNN)，IGD 框架能够完成语义驱动的功能分析、高精度 3D 建模、装配约束推理及运动学分析。

## 🏗️ 系统架构

IGD 框架采用分层架构，包含 Environment Layer（环境层） 和 Functional Layer（功能层），通过全局 Pheromone Field（信息素场） 实现去中心化的自组织协作。

### 核心组件

#### Environment Layer (环境层)

- **TP Agent (Task Planning Agent / 任务规划智能体)** 
  - **职责**：负责解析用户自然语言需求，利用向量数据库检索专家知识，将设计意图分解为可执行的任务列表（如零件设计、3D建模、装配等）。
  - **核心机制**：使用 ACBAC 机制调度任务，维护全局信息素场，协调下层 Agent 的协作。

#### Functional Layer (功能层)

- **PD Agent (Part Design Agent / 零件设计智能体)** 
  - **职责**：专业的需求分析和参数计算，基于设计需求进行专家级的设计分析。
  - **技术支撑**：利用 MKG (Multimodal design Knowledge Graph) 进行检索增强生成 (RAG)，结合 Dify API 工作流及通用 LLM 进行结构化分析。

- **PM Agent (Part Modeling Agent / 零件建模智能体)** 
  - **职责**：生成高精度的 3D 零件模型及建模脚本（OpenSCAD/CADQuery）。
  - **技术支撑**：采用混合提示策略，包括 CRP (Content-Retrieval Prompting) 基于检索的建模和 CGP (Content-Generation Prompting) 基于 SFT 模型的生成式建模。引入 Checker LLM 进行迭代修正。

- **PA Agent (Part Assembly Agent / 零件装配智能体)** 
  - **职责**：装配设计和空间定位，将 3D 零件模型在特定空间位置进行机械装配。
  - **技术支撑**：采用 GART (Graph-based Assembly Relation Transfer) 方法，通过图网络提取几何特征并检索历史装配模式，指导 LLM 生成符合物理约束的装配指令。

### 工作流程 (基于 ACBAC 机制)

1. **任务分解** - TP Agent 使用 DeepSeek API 解析自然语言需求，生成任务包和提案信息素 (PP) 信号。
2. **任务发布** - 发布到全局信息素场。
3. **智能竞标** - 功能层 Agent (PD, PM, PA) 基于自身能力（历史成功率、置信度等）提交提案。
4. **任务分配** - 基于信息素浓度和评分机制，TP Agent 将任务智能分配给最合适的 Agent。
5. **任务执行** - Agent 执行分配到的任务，调用相应的 Dify API (PD, PM, PA)。
6. **结果收集与反馈** - 收集任务结果并反馈至信息素场，强化成功路径。

## 🚀 快速开始

### 环境配置

#### 安装依赖

```bash
pip install -r requirements.txt
```

#### 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API 密钥
# 对应论文中的 General LLM (如 DeepSeek) 及各 Agent 工作流接口
# DEEPSEEK_API_KEY=your_deepseek_api_key
# DIFY_PARAMETER_API_URL=your_dify_parameter_api_url
# DIFY_PARAMETER_API_KEY=your_dify_parameter_api_key
# DIFY_MODELING_API_URL=your_dify_modeling_api_url
# DIFY_MODELING_API_KEY=your_dify_modeling_api_key
# DIFY_ASSEMBLY_API_URL=your_dify_assembly_api_url
# DIFY_ASSEMBLY_API_KEY=your_dify_assembly_api_key
```

### 运行主程序

```bash
cd bee_mas
python main.py
```

### 运行测试

```bash
# 测试 PD Agent (参数分析/设计分析)
python test_parameter_analysis_dify.py

# 测试 PM Agent (三维建模 - CRP/CGP)
python test_modeling_dify.py
```

## 🔧 功能特性

### PD Agent - 语义驱动的设计分析

PD Agent 是系统的核心分析组件，基于多模态知识图谱 (MKG) 和 Dify API 工作流实现：

- **需求解析**：将自然语言需求转化为结构化设计参数和几何描述。
- **知识推理**：利用向量数据库检索历史设计知识，辅助 LLM 进行工程可行性分析。
- **参数计算**：生成精确的工程参数（如模数、齿数、压力角等）。
- **设计建议**：提供基于专家知识库的设计改进建议。

#### 示例输出

```json
{
  "parameters": {
    "模数": 2.0,
    "齿数": 20,
    "压力角": 20,
    "齿宽": 10,
    "孔径": 15
  },
  "units": {
    "长度": "mm",
    "角度": "度"
  },
  "constraints": [
    "使用标准规格",
    "考虑制造可行性"
  ],
  "recommendations": [
    "建议进行详细设计验证"
  ]
}
```

### PM Agent - 混合提示 3D 建模

PM Agent 基于 Dify API 工作流实现，结合了 CRP 和 CGP 两种策略：

- **CRP (Content-Retrieval Prompting)**：基于零件名称检索相似 3D 模型库，利用检索结果作为 Prompt 引导 LLM 生成高精度模型。
- **CGP (Content-Generation Prompting)**：基于 SFT LLM 将几何/功能描述转化为初始建模代码，再由通用 LLM 进行细化。
- **双 LLM 迭代优化**：引入 Checker LLM 对生成的建模脚本（如 OpenSCAD/CADQuery）进行几何准确性检查和修正。
- **参数化设计**：支持参数化模型修改与代码生成。

### PA Agent - 基于图传递的装配设计

PA Agent 基于 Dify API 工作流实现，利用 GART 方法解决 LLM 空间推理能力不足的问题：

- **装配关系识别**：提取零件几何特征、基准要素和功能语义。
- **装配模式检索**：在向量数据库中检索具有相似拓扑结构和配合关系的历史子图。
- **装配图构建**：利用检索到的成熟装配模式作为 Prompt，指导 LLM 推断配合约束、空间位置和运动副类型。
- **干涉检查与运动学推理**：生成装配指令，确保装配体在运动过程中保持几何一致性。

### 智能任务调度 (ACBAC)

- **信息素场调度**：基于全局信息素浓度动态调整任务优先级。
- **负载均衡**：根据 Agent 的能力匹配度、历史成功率和置信度进行智能分配。
- **自适应优化**：通过反馈机制自动强化高效路径，抑制失败路径。

## 📊 系统状态监控

系统提供实时的状态监控功能，对应 IGD 框架的执行反馈：

- 任务分配状态与信息素浓度
- 执行进度跟踪
- Agent 工作负载与 Token 消耗
- 系统性能指标
- 设计迭代日志记录

## 📁 项目结构

```
bee_mas/
├── main.py                           # 主程序入口
├── requirements.txt                  # 依赖包列表
├── README.md                         # 项目说明文档
├── .env.example                      # 环境变量配置模板
├── agents/                           # 智能体模块
│   ├── __init__.py
│   ├── tp_agent.py                   # TP Agent (任务规划/原调度蜂)
│   ├── pd_agent.py                   # PD Agent (零件设计/原工况分析蜂)
│   ├── pm_agent.py                   # PM Agent (零件建模/原三维建模蜂)
│   └── pa_agent.py                   # PA Agent (零件装配/原装配蜂)
├── test_parameter_analysis_dify.py   # PD Agent 测试
├── test_modeling_dify.py             # PM Agent 测试
└── outputs/                          # 输出文件目录
```

## 🤝 贡献指南

欢迎贡献代码和想法！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 LICENSE 文件了解详情。
```
