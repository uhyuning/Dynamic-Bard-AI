# 🎮 Unreal Engine 5 & Python AI: Dynamic Musical Partner

본 프로젝트는 **Spotify 음악 분석**, **ChatGPT 소통**, 그리고 **DQN 강화학습**을 결합하여, 음악 리듬에 맞춰 사용자와 소통하며 스스로 동작을 학습하는 UE5 에이전트 시스템입니다.

## 🚀 Key Features (완성된 기능)

- **🎵 Real-time Music Sense (Spotify API)**: 현재 재생 중인 음악의 장르, BPM, 에너지를 실시간으로 분석하여 에이전트의 감각 데이터로 활용합니다.
- **💬 Smart Conversation (ChatGPT API)**: 에이전트의 현재 행동과 음악 상황을 기반으로 사용자에게 다정하고 맥락에 맞는 한국어 코멘트를 생성합니다.
- **🧠 Intelligent Brain (DQN Reinforcement Learning)**: Deep Q-Network를 통해 음악의 분위기에 가장 적합한 행동(전진, 회전 등)을 스스로 선택하고 학습합니다.

## 📂 Project Structure

```text
UE5_AI_RL_Project/
├── AIServer/               # API 통신 및 메인 서버 레이더
│   ├── server.py           # FastAPI 메인 서버 (DQN/Spotify/GPT 통합)
│   ├── gpt_client.py       # OpenAI GPT 통신 및 폴백 로직
│   └── spotify_mock.py     # 음악 데이터 공급 모듈
├── RL_Trainer/             # 강화학습 핵심 모듈
│   ├── models/             # DQN 신경망 구조
│   └── utils/              # ReplayBuffer 등 학습 보조 도구
├── Shared/                 # 서버-언리얼 간 공통 프로토콜 정의
└── UnrealProject/          # UE5 시뮬레이션 환경 (진행 예정)