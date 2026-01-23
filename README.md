# IGD Framework Implementation

Implementing semantics-driven end-to-end intelligent mechanical design

## 🐝 System Overview

An engineering implementation of the IGD (Intelligent Generative Design) framework, which is a semantics-driven unified generative design framework. The system employs an ant-colony-inspired ACBAC (Ant-Colony Bionic Agent Collaboration) multi-agent collaboration mechanism, achieving full-process automation from natural language requirements to complex mechanical product design, modeling, and assembly.

By integrating General Large Language Models (LLMs), Supervised Fine-Tuned Models (SFT LLMs), and specific Task Neural Networks (TNNs), the IGD framework is capable of completing semantics-driven functional analysis, high-precision 3D modeling, assembly constraint reasoning, and kinematic analysis.

## 🏗️ System Architecture

The IGD framework adopts a layered architecture, comprising the Environment Layer and the Functional Layer, enabling decentralized self-organizing collaboration through a global Pheromone Field.

### Core Components

#### Environment Layer

- **TP Agent (Task Planning Agent)** 
  - **Responsibilities**: Responsible for parsing user natural language requirements, utilizing vector databases to retrieve expert knowledge, and decomposing design intent into executable task lists (e.g., part design, 3D modeling, assembly, etc.).
  - **Core Mechanism**: Uses the ACBAC mechanism to schedule tasks, maintains the global pheromone field, and coordinates collaboration among lower-layer Agents.

#### Functional Layer

- **PD Agent (Part Design Agent)** 
  - **Responsibilities**: Professional requirement analysis and parameter calculation, performing expert-level design analysis based on design requirements.
  - **Technical Support**: Utilizes MKG (Multimodal design Knowledge Graph) for Retrieval-Augmented Generation (RAG), combined with Dify API workflows and general LLMs for structured analysis.

- **PM Agent (Part Modeling Agent)** 
  - **Responsibilities**: Generates high-precision 3D part models and modeling scripts (OpenSCAD/CADQuery).
  - **Technical Support**: Adopts a hybrid prompting strategy, including CRP (Content-Retrieval Prompting) for retrieval-based modeling and CGP (Content-Generation Prompting) for SFT model-based generative modeling. Introduces a Checker LLM for iterative correction.

- **PA Agent (Part Assembly Agent)** 
  - **Responsibilities**: Assembly design and spatial positioning, mechanically assembling 3D part models at specific spatial locations.
  - **Technical Support**: Employs the GART (Graph-based Assembly Relation Transfer) method, extracting geometric features through graph networks and retrieving historical assembly patterns to guide the LLM in generating assembly instructions that comply with physical constraints.

### Workflow (Based on ACBAC Mechanism)

1. **Task Decomposition** - TP Agent uses the DeepSeek API to parse natural language requirements, generating task packages and Proposal Pheromone (PP) signals.
2. **Task Posting** - Published to the global pheromone field.
3. **Intelligent Bidding** - Functional Layer Agents (PD, PM, PA) submit proposals based on their capabilities (historical success rates, confidence, etc.).
4. **Task Allocation** - Based on pheromone concentration and scoring mechanisms, the TP Agent intelligently allocates tasks to the most suitable Agent.
5. **Task Execution** - Agents execute assigned tasks, calling the corresponding Dify APIs (PD, PM, PA).
6. **Result Collection & Feedback** - Collects task results and feeds them back to the pheromone field, reinforcing successful paths.

## 🚀 Quick Start

### Environment Configuration

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

```bash
# Copy environment variable template
cp .env.example .env

# Edit the .env file and fill in your API keys
# Corresponds to the General LLM (e.g., DeepSeek) in the paper and the workflow interfaces for each Agent
# DEEPSEEK_API_KEY=your_deepseek_api_key
# DIFY_PARAMETER_API_URL=your_dify_parameter_api_url
# DIFY_PARAMETER_API_KEY=your_dify_parameter_api_key
# DIFY_MODELING_API_URL=your_dify_modeling_api_url
# DIFY_MODELING_API_KEY=your_dify_modeling_api_key
# DIFY_ASSEMBLY_API_URL=your_dify_assembly_api_url
# DIFY_ASSEMBLY_API_KEY=your_dify_assembly_api_key
```

### Run Main Program

```bash
cd bee_mas
python main.py
```

### Run Tests

```bash
# Test PD Agent (Parameter Analysis/Design Analysis)
python test_parameter_analysis_dify.py

# Test PM Agent (3D Modeling - CRP/CGP)
python test_modeling_dify.py
```

## 🔧 Feature Highlights

### PD Agent - Semantics-Driven Design Analysis

The PD Agent is the core analysis component of the system, implemented based on the Multimodal Knowledge Graph (MKG) and Dify API workflows:

- **Requirement Parsing**: Transforms natural language requirements into structured design parameters and geometric descriptions.
- **Knowledge Reasoning**: Utilizes vector databases to retrieve historical design knowledge, assisting the LLM in engineering feasibility analysis.
- **Parameter Calculation**: Generates precise engineering parameters (e.g., module, number of teeth, pressure angle, etc.).
- **Design Suggestions**: Provides design improvement suggestions based on the expert knowledge base.

#### Example Output

```json
{
  "parameters": {
    "module": 2.0,
    "teeth_number": 20,
    "pressure_angle": 20,
    "face_width": 10,
    "bore_diameter": 15
  },
  "units": {
    "length": "mm",
    "angle": "degrees"
  },
  "constraints": [
    "Use standard specifications",
    "Consider manufacturing feasibility"
  ],
  "recommendations": [
    "Suggest detailed design verification"
  ]
}
```

### PM Agent - Hybrid Prompting 3D Modeling

The PM Agent is implemented based on the Dify API workflow, combining two strategies: CRP and CGP.

- **CRP (Content-Retrieval Prompting)**: Retrieves similar 3D model libraries based on part names and uses the retrieval results as Prompts to guide the LLM in generating high-precision models.
- **CGP (Content-Generation Prompting)**: Uses an SFT LLM to transform geometric/functional descriptions into initial modeling code, which is then refined by a general LLM.
- **Dual LLM Iterative Optimization**: Introduces a Checker LLM to perform geometric accuracy checks and corrections on the generated modeling scripts (e.g., OpenSCAD/CADQuery).
- **Parametric Design**: Supports parametric model modification and code generation.

### PA Agent - Graph-Based Transfer Assembly Design

The PA Agent is implemented based on the Dify API workflow, utilizing the GART method to address the LLM's lack of spatial reasoning capabilities:

- **Assembly Relation Identification**: Extracts part geometric features, datum elements, and functional semantics.
- **Assembly Pattern Retrieval**: Retrieves historical subgraphs with similar topological structures and mating relationships in the vector database.
- **Assembly Graph Construction**: Uses retrieved mature assembly patterns as Prompts to guide the LLM in inferring mating constraints, spatial positions, and kinematic pair types.
- **Interference Checking & Kinematic Reasoning**: Generates assembly instructions to ensure geometric consistency during the motion of the assembly.

### Intelligent Task Scheduling (ACBAC)

- **Pheromone Field Scheduling**: Dynamically adjusts task priorities based on global pheromone concentration.
- **Load Balancing**: Intelligently allocates tasks based on Agent capability match, historical success rates, and confidence.
- **Adaptive Optimization**: Automatically reinforces efficient paths and suppresses failed paths through feedback mechanisms.

## 📊 System Status Monitoring

The system provides real-time status monitoring functions, corresponding to the execution feedback of the IGD framework:

- Task allocation status and pheromone concentration
- Execution progress tracking
- Agent workload and Token consumption
- System performance metrics
- Design iteration log recording

## 📁 Project Structure

```text
bee_mas/
├── main.py                           # Main program entry
├── requirements.txt                  # Dependency list
├── README.md                         # Project documentation
├── .env.example                      # Environment variable configuration template
├── agents/                           # Agent modules
│   ├── __init__.py
│   ├── tp_agent.py                   # TP Agent (Task Planning)
│   ├── pd_agent.py                   # PD Agent (Part Design)
│   ├── pm_agent.py                   # PM Agent (Part Modeling)
│   └── pa_agent.py                   # PA Agent (Part Assembly)
├── test_parameter_analysis_dify.py   # PD Agent Test
├── test_modeling_dify.py             # PM Agent Test
└── outputs/                          # Output files directory
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
