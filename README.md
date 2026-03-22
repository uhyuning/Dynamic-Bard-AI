# Dynamic Bard AI

> 사용자와 대화하며 기분을 파악하고, 어울리는 음악과 맵 분위기를 실시간으로 바꿔주는 UE5 AI 캐릭터 시스템

---

## 프로젝트 개요

사용자가 AI 캐릭터와 채팅을 하면:

1. **GPT**가 대화 내용을 분석해 감정(Sentiment)과 에너지(Arousal)를 추출
2. **강화학습 모델(MasterAgent)**이 현재 상황에 맞는 음악 방향을 결정
3. **Spotify API**에서 그 분위기에 맞는 실제 곡을 검색
4. **언리얼5**에서 AI 대사 표시, 음악 재생, 맵 분위기 변경

사용자가 노래를 스킵하거나 좋아요를 누를 때마다 AI가 더 잘 맞는 곡을 추천하도록 지속 학습합니다.

---

## 아키텍처

```
UE5_AI_RL_Project/
├── AIServer/               ← Python FastAPI 서버 (시스템의 두뇌)
│   ├── server.py           ← 메인 서버, 모든 모듈 통합
│   ├── gpt_client.py       ← GPT API 감정 분석
│   ├── spotify_client.py   ← Spotify 음악 검색
│   └── spotify_mock.py     ← Spotify 미연결 시 Mock 데이터
├── RL_Trainer/             ← 강화학습 엔진
│   ├── train.py            ← DQN 학습 루프 (오프라인/온라인)
│   ├── models/model.py     ← MasterAgent 신경망 구조
│   └── memory.py           ← Prioritized Experience Replay
├── Shared/
│   └── protocol.py         ← 서버-UE5 간 공통 데이터 규격
├── Dynamic_Bard_AI_UE5/    ← 언리얼5 게임 프로젝트
│   └── Source/.../BardAI/  ← C++ 서버 통신 컴포넌트
├── .env                    ← API 키 (Git 제외)
├── requirements.txt        ← Python 의존성
└── master_agent_brain.pth  ← 학습된 모델 가중치
```

---

## 데이터 흐름

```
[사용자] "오늘 좀 우울해..."
    |
    | HTTP POST /chat
    v
[AIServer/server.py]
    |
    ├── [GPT API]       → 감정: -0.7 / 에너지: 0.2 / AI 대사 생성
    ├── [MasterAgent]   → 음악 방향 결정: "잔잔한 곡 (Action 0)"
    └── [Spotify API]   → Lo-fi 트랙 검색, 30초 미리듣기 URL 반환
    |
    | HTTP 응답
    v
[언리얼5]
    ├── AI 대사 표시 (말풍선)
    ├── 음악 재생 (사운드 에셋 교체)
    └── 맵 분위기 변경 (조명, 포그, 날씨)

[사용자가 스킵] → POST /feedback → RL 보상: -1.5 → 모델 업데이트
[사용자가 좋아요] → POST /feedback → RL 보상: +2.0 → 모델 업데이트
```

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| AI 서버 | Python, FastAPI, Uvicorn |
| 감정 분석 | OpenAI GPT API |
| 음악 추천 | Spotify Web API (spotipy) |
| 강화학습 | PyTorch, DQN, Prioritized Experience Replay, Target Network |
| 게임 엔진 | Unreal Engine 5 (C++) |
| 통신 | HTTP REST (UE5 ↔ Python) |

---

## 강화학습 구조

### MasterAgent 입력 (STATE_DIM = 12)

| 인덱스 | 의미 | 범위 |
|--------|------|------|
| 0 | 사용자 감정 | -1.0 (슬픔) ~ +1.0 (기쁨) |
| 1 | 사용자 에너지 | 0.0 (지침) ~ 1.0 (활발) |
| 2 | 음악 BPM | 정규화된 빠르기 |
| 3 | 음악 에너지 | Spotify energy 값 |
| 4 | 음악 긍정도 | Spotify valence 값 |
| 5~8 | 음악 장르 원핫 | 잔잔/신남/감성/집중 |
| 9 | 대화 횟수 | 세션 내 누적 |
| 10 | 세션 시간 | 경과 시간(초) |
| 11 | 이전 행동 | 직전 선택 장르 |

### 출력 (ACTION_DIM = 4)

| 행동 | 음악 스타일 | 예시 장르 |
|------|-----------|---------|
| 0 | 잔잔 | Lo-fi, Ambient |
| 1 | 신남 | K-Pop, Pop |
| 2 | 감성 | Indie, R&B |
| 3 | 집중 | Classical, Piano |

### 보상 시스템

| 사용자 행동 | 보상 |
|-----------|------|
| 좋아요 | +2.0 |
| 다시 듣기 | +1.5 |
| 끝까지 들음 | +0.7 |
| 스킵 | -1.5 |

---

## 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. API 키 설정

프로젝트 루트에 `.env` 파일 생성:

```env
OPENAI_API_KEY=sk-...
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

> Spotify 키가 없어도 됩니다. 없으면 자동으로 Mock 모드로 전환됩니다.

### 3. AI 서버 실행

```bash
python AIServer/server.py
```

브라우저에서 `http://localhost:8000` 열어 `"status": "online"` 확인.

### 4. (선택) 오프라인 사전 학습

```bash
python RL_Trainer/train.py
```

시뮬레이션 데이터로 기초 학습을 먼저 수행합니다.

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/` | 서버 헬스체크 |
| `POST` | `/chat` | 채팅 메시지 처리 (핵심) |
| `POST` | `/feedback` | 음악 피드백 수신 (좋아요/스킵) |
| `GET` | `/status` | AI 학습 현황 |
| `GET` | `/now-playing` | 현재 재생 트랙 |
| `POST` | `/act` | UE5 위치 정보로 행동 결정 |

---

## UE5 연동

`BardAIManager` C++ 컴포넌트를 캐릭터 Blueprint에 추가하면 됩니다.

**Blueprint에서 연결 가능한 이벤트:**

| 이벤트 | 발생 시점 | 사용 예 |
|--------|---------|--------|
| `OnChatReply` | AI 응답 도착 | 말풍선, 자막 표시 |
| `OnMusicChange` | 음악 장르 변경 | 사운드 에셋 교체 |
| `OnAtmosphereChange` | 감정/에너지 변화 | 조명, 포그, 날씨 |
| `OnRequestFailed` | 서버 오류 | 에러 UI 표시 |

---

## 담당 영역

| 영역 | 경로 |
|------|------|
| AI 서버 & API 연동 | `AIServer/` |
| 강화학습 모델 | `RL_Trainer/` |
| UE5 통신 컴포넌트 | `Dynamic_Bard_AI_UE5/Source/.../BardAI/` |
| UE5 그래픽 & 에셋 | `Dynamic_Bard_AI_UE5/Content/` |

---

## 가이드 문서

- [전체 파일 설명서](PROJECT_OVERVIEW.md) — 각 파일이 무엇을 하는지, 처음 보는 사람도 이해할 수 있게 정리
- [UE5 에셋 교체 가이드](Dynamic_Bard_AI_UE5/ARTIST_GUIDE.md) — 캐릭터/음악/맵을 UE5에서 연결하는 단계별 안내
