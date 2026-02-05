# Unreal Engine 5 & Python AI Reinforcement Learning Project

본 프로젝트는 UE5 시뮬레이션 환경과 Python 기반 AI 서버 간의 연동을 통한 강화학습(Reinforcement Learning) 시스템 구축을 목표로 합니다.

## 📂 Project Structure



```text
UE5_AI_RL_Project/
├── AIServer/               # API Communication Layer
│   ├── server.py           # FastAPI Main Server
│   └── inference.py        # Model Inference Script
├── RL_Trainer/             # Reinforcement Learning Module
│   ├── models/             # Neural Network Architectures
│   │   └── model.py
│   ├── envs/               # Custom RL Environments
│   ├── checkpoints/        # Saved Model Weights
│   ├── memory.py           # Replay Buffer Logic
│   └── train.py            # Main Training Loop
├── Shared/                 # Common Data Interfaces
│   └── protocol.py         # State/Action Data Definitions
└── UnrealProject/          # UE5 Simulation Environment
    ├── Plugins/            # Unreal Engine Plugins (e.g., VaRest)
    ├── Content/            # Game Assets and Blueprints
    └── MyAIRLProject.uproject


## 🗺️ Roadmap
- [v] Phase 1: Project Architecture & API Communication Setup
- [ ] Phase 2: Basic RL Agent Implementation (DQN)
- [ ] Phase 3: Reward Function Tuning in UE5
- [ ] Phase 4: Real-time Inference & Performance Optimization

## ❓ Troubleshooting (FAQ)
- **Port 8000 is already in use**: 
  - 서버 실행 시 8000번 포트가 사용 중이라면 `AIServer/server.py`에서 `port` 번호를 변경하거나 해당 포트를 점유 중인 프로세스를 종료하십시오.
- **VaRest Plugin Error**: 
  - UE5 실행 시 플러그인 누락 경고가 발생하면 `UnrealProject/Plugins` 폴더에 VaRest 플러그인이 정상적으로 배치되었는지 확인하십시오.
- **Import Error**: 
  - 라이브러리 인식 문제가 발생할 경우 프로젝트 루트 폴더에서 `pip install -r requirements.txt`를 재수행하십시오.