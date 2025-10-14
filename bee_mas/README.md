# Bee-MAS 智能多Agent系统

## 🐝 系统概述

Bee-MAS是一个基于蜂群智能的多Agent系统，专门用于工程设计和任务调度。系统模拟了蜜蜂社会的分工协作机制，通过智能工蜂的协作来完成复杂的工程任务。系统集成了Dify AI工作流和DeepSeek API，提供智能化的任务分解、参数分析、3D建模和装配设计功能。

## 🏗️ 系统架构

### 核心组件

1. **调度蜂 (SchedulerBee)** - 负责任务分解、分配和协调，使用DeepSeek API进行智能任务分析
2. **工况分析蜂** - 专业的需求分析和参数计算，基于Dify API工作流
3. **三维建模蜂** - 3D建模和OpenSCAD脚本生成，基于Dify API工作流
4. **装配蜂** - 装配设计和空间定位，基于Dify API工作流

### 工作流程

1. **任务分解** - 使用DeepSeek API将用户需求智能分解为子任务
2. **任务发布** - 发布到任务公告板
3. **智能竞标** - 工蜂自动分析并提交提案
4. **任务分配** - 基于评分智能分配任务
5. **任务执行** - 工蜂执行分配到的任务，调用相应的Dify API
6. **结果收集** - 收集和整合任务结果

## 🚀 快速开始

### 环境配置

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的API密钥
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
# 测试参数分析蜂
python test_parameter_analysis_dify.py

# 测试三维建模蜂
python test_modeling_dify.py
```

## 🔧 功能特性

### 工况分析蜂 - 参数生成

工况分析蜂是系统的核心组件，基于Dify API工作流实现：

- **需求分析** - 将自然语言需求转化为结构化参数
- **参数计算** - 生成精确的工程参数
- **约束识别** - 识别设计约束和限制条件
- **设计建议** - 提供专业的设计建议

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

### 三维建模蜂 - OpenSCAD代码生成

基于Dify API工作流实现：

- **3D建模** - 根据参数生成3D模型
- **OpenSCAD脚本** - 生成可执行的OpenSCAD代码
- **模型文件** - 输出标准3D模型文件
- **参数化设计** - 支持参数化模型修改

### 装配蜂 - 装配设计

基于Dify API工作流实现：

- **装配设计** - 设计部件装配关系
- **空间定位** - 确定部件空间位置
- **干涉检查** - 检查装配干涉问题
- **装配脚本** - 生成装配指令

### 智能任务调度

- **依赖管理** - 自动管理任务间的依赖关系
- **负载均衡** - 智能分配任务给最合适的工蜂
- **进度跟踪** - 实时监控任务执行状态
- **错误处理** - 自动处理任务执行异常

## 📊 系统状态监控

系统提供实时的状态监控功能：

- 任务分配状态
- 执行进度跟踪
- 工蜂工作负载
- 系统性能指标
- 数据流日志记录

## 🔮 未来规划

### 短期目标
- [x] 基础任务执行引擎
- [x] 工况分析蜂参数生成
- [x] 三维建模蜂OpenSCAD集成
- [x] 装配蜂装配脚本生成
- [ ] Web界面开发
- [ ] 任务模板系统

### 长期目标
- [ ] 性能优化和并发处理
- [ ] 更多工程领域支持
- [ ] 可视化工作流编辑器
- [ ] 分布式任务执行

## 🤝 贡献指南

欢迎贡献代码和想法！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🔧 API配置

### DeepSeek API配置

```bash
# 必需
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
```

### Dify API配置

```bash
# 工况分析蜂配置
DIFY_PARAMETER_API_URL=https://api.dify.ai/v1/workflows/run
DIFY_PARAMETER_API_KEY=your_dify_parameter_api_key

# 三维建模蜂配置
DIFY_MODELING_API_URL=https://api.dify.ai/v1/workflows/run
DIFY_MODELING_API_KEY=your_dify_modeling_api_key

# 装配蜂配置
DIFY_ASSEMBLY_API_URL=https://api.dify.ai/v1/workflows/run
DIFY_ASSEMBLY_API_KEY=your_dify_assembly_api_key
```

## 📁 项目结构

```
bee_mas/
├── main.py                    # 主程序入口
├── requirements.txt           # 依赖包列表
├── README.md                 # 项目说明文档
├── .env.example              # 环境变量配置模板
├── agents/                   # 智能工蜂模块
│   ├── __init__.py
│   ├── parameter_analysis_bee.py  # 工况分析蜂
│   ├── modeling_bee.py           # 三维建模蜂
│   └── assembly_bee.py           # 装配蜂
├── test_parameter_analysis_dify.py  # 参数分析测试
├── test_modeling_dify.py           # 三维建模测试
└── outputs/                  # 输出文件目录
```

## 🐛 故障排除

### 常见问题

1. **API密钥未配置**
   - 确保.env文件中的API密钥已正确配置
   - 检查API密钥是否有效

2. **Dify API端点错误**
   - 确保使用的是API端点而不是网页链接
   - 正确的API端点应包含"/v1/"或"/api/"路径

3. **任务执行失败**
   - 检查data_flow.log文件获取详细错误信息
   - 确认网络连接正常

##  联系方式

如有问题或建议，请通过以下方式联系：

- 项目Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com

---

**Bee-MAS** - 让工程设计更智能，让协作更高效！ 🐝✨





