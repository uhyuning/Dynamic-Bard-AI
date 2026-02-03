# 🎮 UE5 AI Reinforcement Learning Project

언리얼 엔진 5(UE5)와 파이썬 강화학습(RL)을 연동한 지능형 에이전트 개발 프로젝트입니다.

---

## 📂 프로젝트 구조 (Project Structure)

```text
UE5_AI_RL_Project/
├── UnrealProject/          # UE5 프로젝트 (환경 및 에이전트 바디)
│   └── Plugins/            # 전용 플러그인 (ML-Agents, Socket.io 등)
├── AIServer/               # 실시간 추론 및 서비스 서버 (두뇌)
│   ├── server.py           # UE5와 실시간 통신 (FastAPI 기반)
│   └── inference.py        # 학습된 .pth 모델 로드 및 실행
├── RL_Trainer/             # 강화학습 전용 코드 (학습장)
│   ├── envs/               # 언리얼 환경과의 연결 설정 (Gymnasium)
│   ├── models/             # RL 알고리즘 (PPO, DQN, SAC 등)
│   ├── train.py            # 학습 실행 메인 스크립트
│   └── checkpoints/        # 학습 단계별 가중치 저장소
├── Shared/                 # 데이터 규격 (State/Action 정의 공유)
└── requirements.txt        # 필수 라이브러리 (torch, gymnasium 등)