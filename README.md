IGD Framework Implementation

Implementation of a Semantic-Driven End-to-End Intelligent Mechanical Design

🐝 System Overview

Engineering implementation of the IGD (Intelligent Generative Design) framework, a unified semantic-driven generative design framework. The system adopts an Ant-Colony inspired ACBAC (Ant-Colony Bionic Agent Collaboration) multi-agent collaboration mechanism, achieving full-process automation from natural language requirements to the design, modeling, and assembly of complex mechanical products.

By integrating General Large Language Models (LLMs), Supervised Fine-Tuned Models (SFT LLMs), and specialized Task Neural Networks (TNNs), the IGD framework is capable of performing semantic-driven functional analysis, high-precision 3D modeling, assembly constraint reasoning, and kinematic analysis.

🏗️ System Architecture

The IGD framework employs a layered architecture, consisting of the Environment Layer and the Functional Layer, achieving decentralized self-organizing collaboration through a global Pheromone Field.

Core Components

Environment Layer

• TP Agent (Task Planning Agent)

  • Responsibilities: Parses user natural language requirements, retrieves expert knowledge using a vector database, and decomposes design intent into an executable task list (e.g., part design, 3D modeling, assembly).

  • Core Mechanism: Uses the ACBAC mechanism for task scheduling, maintains the global pheromone field, and coordinates collaboration among lower-level Agents.

Functional Layer

• PD Agent (Part Design Agent)

  • Responsibilities: Specialized requirement analysis and parameter calculation, performing expert-level design analysis based on design requirements.

  • Technical Support: Utilizes MKG (Multimodal design Knowledge Graph) for Retrieval-Augmented Generation (RAG), combined with Dify API workflows and General LLMs for structured analysis.

• PM Agent (Part Modeling Agent)

  • Responsibilities: Generates high-precision 3D part models and modeling scripts (OpenSCAD/CADQuery).

  • Technical Support: Employs hybrid prompting strategies, including CRP (Content-Retrieval Prompting) for retrieval-based modeling and CGP (Content-Generation Prompting) for generation-based modeling using SFT models. Introduces a Checker LLM for iterative correction.

• PA Agent (Part Assembly Agent)

  • Responsibilities: Assembly design and spatial positioning, performing mechanical assembly of 3D part models in specific spatial locations.

  • Technical Support: Uses the GART (Graph-based Assembly Relation Transfer) method, extracting geometric features via graph networks and retrieving historical assembly patterns to guide the LLM in generating assembly instructions that adhere to physical constraints.

Workflow (Based on the ACBAC Mechanism)

1. Task Decomposition - TP Agent uses the DeepSeek API to parse natural language requirements, generating task packages and Proposal Pheromone (PP) signals.
2. Task Publishing - Tasks are published to the global pheromone field.
3. Agent Bidding - Functional layer Agents (PD, PM, PA) submit proposals based on their capabilities (historical success rate, confidence, etc.).
4. Task Assignment - Based on pheromone concentration and a scoring mechanism, the TP Agent intelligently assigns tasks to the most suitable Agent.
5. Task Execution - The Agent executes the assigned task by calling the corresponding Dify API (PD, PM, PA).
6. Result Collection & Feedback - Task results are collected and fed back into the pheromone field, reinforcing successful paths.

🚀 Quick Start

Environment Configuration

Install Dependencies

pip install -r requirements.txt


Configure Environment Variables

# Copy the environment variable template
cp .env.example .env

# Edit the .env file, fill in your API keys
# Corresponding to the General LLM (e.g., DeepSeek) and Agent workflow interfaces mentioned in the paper
# DEEPSEEK_API_KEY=your_deepseek_api_key
# DIFY_PARAMETER_API_URL=your_dify_parameter_api_url
# DIFY_PARAMETER_API_KEY=your_dify_parameter_api_key
# DIFY_MODELING_API_URL=your_dify_modeling_api_url
# DIFY_MODELING_API_KEY=your_dify_modeling_api_key
# DIFY_ASSEMBLY_API_URL=your_dify_assembly_api_url
# DIFY_ASSEMBLY_API_KEY=your_dify_assembly_api_key


Run the Main Program

cd bee_mas
python main.py


Run Tests

# Test PD Agent (Parameter Analysis/Design Analysis)
python test_parameter_analysis_dify.py

# Test PM Agent (3D Modeling - CRP/CGP)
python test_modeling_dify.py


🔧 Features

PD Agent - Semantic-Driven Design Analysis

PD Agent is the core analytical component of the system, implemented based on the Multimodal Knowledge Graph (MKG) and Dify API workflows:

• Requirement Parsing: Transforms natural language requirements into structured design parameters and geometric descriptions.

• Knowledge Reasoning: Uses vector database retrieval of historical design knowledge to assist LLMs in engineering feasibility analysis.

• Parameter Calculation: Generates precise engineering parameters (e.g., modulus, number of teeth, pressure angle).

• Design Recommendations: Provides design improvement suggestions based on an expert knowledge base.

Example Output

{
  "parameters": {
    "modulus": 2.0,
    "number_of_teeth": 20,
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
    "Consider manufacturability"
  ],
  "recommendations": [
    "Perform detailed design validation"
  ]
}


PM Agent - Hybrid Prompting 3D Modeling

PM Agent is implemented based on Dify API workflows, combining CRP and CGP strategies:

• CRP (Content-Retrieval Prompting): Retrieves similar 3D model libraries based on part names, using the retrieved results as prompts to guide the LLM in generating high-precision models.

• CGP (Content-Generation Prompting): Uses SFT LLMs to convert geometric/functional descriptions into initial modeling code, which is then refined by a General LLM.

• Dual LLM Iterative Optimization: Introduces a Checker LLM to perform geometric accuracy checks and corrections on generated modeling scripts (e.g., OpenSCAD/CADQuery).

• Parametric Design: Supports parametric model modifications and code generation.

PA Agent - Graph-based Assembly Design

PA Agent is implemented based on Dify API workflows, utilizing the GART method to address LLM shortcomings in spatial reasoning:

• Assembly Relation Recognition: Extracts part geometric features, datum elements, and functional semantics.

• Assembly Pattern Retrieval: Retrieves historical subgraphs with similar topological structures and mating relationships from a vector database.

• Assembly Graph Construction: Uses retrieved mature assembly patterns as prompts to guide the LLM in inferring mating constraints, spatial positions, and joint types.

• Interference Checking & Kinematic Reasoning: Generates assembly instructions ensuring geometric consistency during motion.

Intelligent Task Scheduling (ACBAC)

• Pheromone Field Scheduling: Dynamically adjusts task priority based on global pheromone concentration.

• Load Balancing: Intelligently assigns tasks based on Agent capability matching, historical success rate, and confidence.

• Adaptive Optimization: Automatically reinforces efficient paths and suppresses failure paths through feedback mechanisms.

📊 System Status Monitoring

The system provides real-time status monitoring, corresponding to the execution feedback of the IGD framework:

• Task assignment status and pheromone concentration

• Execution progress tracking

• Agent workload and Token consumption

• System performance metrics

• Design iteration log recording

📁 Project Structure


bee_mas/
├── main.py                           # Main program entry point
├── requirements.txt                  # Dependency list
├── README.md                         # Project documentation
├── .env.example                      # Environment variable configuration template
├── agents/                           # Agent modules
│   ├── __init__.py
│   ├── tp_agent.py                   # TP Agent (Task Planning)
│   ├── pd_agent.py                   # PD Agent (Part Design)
│   ├── pm_agent.py                   # PM Agent (Part Modeling)
│   └── pa_agent.py                   # PA Agent (Part Assembly)
├── test_parameter_analysis_dify.py   # PD Agent test
├── test_modeling_dify.py             # PM Agent test
└── outputs/                          # Output directory


🤝 Contribution Guidelines

Contributions of code and ideas are welcome! Please follow these steps:

1. Fork the project
2. Create a feature branch (git checkout -b feature/AmazingFeature)
3. Commit your changes (git commit -m 'Add some AmazingFeature')
4. Push to the branch (git push origin feature/AmazingFeature)
5. Open a Pull Request

📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
