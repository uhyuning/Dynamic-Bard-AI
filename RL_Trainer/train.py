"""
RL_Trainer/train.py — 오프라인 / 온라인 학습 모듈 (v2.0)

[역할]
- 단독 실행(offline) : 시뮬레이션 데이터로 모델을 사전 학습합니다.
- 서버에서 임포트(online): push_experience()로 실제 대화 데이터를 받아 학습합니다.

[STATE_DIM = 12]
  0  sentiment_score    (-1 ~ 1)
  1  arousal_level      (0 ~ 1)
  2  bpm_norm           (0 ~ 1)
  3  music_energy       (0 ~ 1)
  4  music_valence     (0 ~ 1)  ← Spotify valence (음악 긍정도)
  5  genre_kpop         (0 or 1)
  6  genre_lofi         (0 or 1)
  7  genre_hiphop       (0 or 1)
  8  genre_classical    (0 or 1)
  9  turns_norm         (0 ~ 1)
  10 session_time_norm  (0 ~ 1)
  11 prev_action_norm   (0 ~ 1)

[ACTION_DIM = 4]
  0: 잔잔한 음악 (Lo-fi)
  1: 신나는 음악 (K-Pop)
  2: 감성적인 음악 (Hip-hop)
  3: 집중용 음악 (Classical)
"""

import os
import sys
import random
import numpy as np
import torch
import torch.optim as optim
import torch.nn as nn

# train.py가 단독 실행될 때와 서버에서 임포트될 때 모두 경로가 맞도록 처리
_trainer_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_trainer_dir)
if _trainer_dir not in sys.path:
    sys.path.insert(0, _trainer_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from models.model import MasterAgent, STATE_DIM, ACTION_DIM
from memory import PrioritizedMemory

# ── 하이퍼파라미터 ────────────────────────────────────────────────────────────
BATCH_SIZE = 32
LR = 0.001
GAMMA = 0.99
TARGET_UPDATE_INTERVAL = 100
SAVE_PATH = os.path.join(_project_root, "master_agent_brain.pth")

# ── 행동 이름 매핑 ────────────────────────────────────────────────────────────
ACTION_NAMES = {
    0: "잔잔한 음악 (Lo-fi)",
    1: "신나는 음악 (K-Pop)",
    2: "감성적인 음악 (Hip-hop)",
    3: "집중용 음악 (Classical)",
}

ACTION_GENRE = {
    0: "Lo-fi",
    1: "K-Pop",
    2: "Hip-hop",
    3: "Classical",
}

# ── 모델 / 메모리 / 옵티마이저 초기화 ────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = MasterAgent(STATE_DIM, ACTION_DIM).to(device)
target_model = MasterAgent(STATE_DIM, ACTION_DIM).to(device)
target_model.load_state_dict(model.state_dict())
target_model.eval()

memory = PrioritizedMemory(capacity=10000)
optimizer = optim.Adam(model.parameters(), lr=LR)
criterion = nn.MSELoss()

total_episodes = 0

# ── 체크포인트 로드 ───────────────────────────────────────────────────────────
def load_checkpoint():
    global total_episodes
    if not os.path.exists(SAVE_PATH):
        print("🐣 새로운 지능으로 처음부터 시작합니다.")
        return

    try:
        checkpoint = torch.load(SAVE_PATH, map_location=device)
        state_dict = checkpoint['model_state_dict'] if isinstance(checkpoint, dict) else checkpoint

        # 아키텍처 변경 감지: 입력 크기가 다르면 새로 시작
        first_weight = next(iter(state_dict.values()))
        if first_weight.shape[-1] != STATE_DIM:
            print(f"[WARN] 저장된 모델의 STATE_DIM({first_weight.shape[-1]})이 "
                  f"현재({STATE_DIM})와 다릅니다. 새로 시작합니다.")
            os.remove(SAVE_PATH)
            return

        model.load_state_dict(state_dict)
        target_model.load_state_dict(state_dict)
        if isinstance(checkpoint, dict):
            total_episodes = checkpoint.get('total_episodes', 0)
        print(f"[OK] 기존 지능을 불러왔습니다. (누적 학습 횟수: {total_episodes}회)")

    except Exception as e:
        print(f"[WARN] 체크포인트 로드 실패 ({e}). 새로 시작합니다.")
        if os.path.exists(SAVE_PATH):
            os.remove(SAVE_PATH)

# ── 체크포인트 저장 ───────────────────────────────────────────────────────────
def save_checkpoint():
    torch.save({
        'model_state_dict': model.state_dict(),
        'total_episodes': total_episodes
    }, SAVE_PATH)

# ── 보상 함수 ────────────────────────────────────────────────────────────────
def compute_reward(sentiment: float, action: int) -> float:
    """
    감정(sentiment)과 선택된 행동(action)의 궁합으로 보상을 계산합니다.
      sentiment < -0.3 (우울/스트레스) → 잔잔(0) or 감성(2)이 좋음
      sentiment > +0.3 (긍정/신남)     → 신나는(1)이 좋음
      그 외 (중립)                     → 집중(3)이 적합
    """
    if sentiment < -0.3:
        rewards = {0: 0.9, 1: -0.7, 2: 0.6, 3: 0.2}
    elif sentiment > 0.3:
        rewards = {0: -0.2, 1: 1.0, 2: 0.4, 3: 0.1}
    else:
        rewards = {0: 0.3, 1: 0.2, 2: 0.4, 3: 0.7}
    return rewards[action]

# ── Spotify 피드백 보상 계산 ──────────────────────────────────────────────────
# 사용자의 실제 반응이 RL의 가장 강력한 신호입니다.
FEEDBACK_BASE_REWARDS = {
    "liked":    2.0,   # 명시적 좋아요 → 최고 보상
    "replayed": 1.5,   # 다시 듣기 → 매우 좋음
    "listened": 0.8,   # 완청 → 좋음 (청취율 반영)
    "skipped":  -1.5,  # 스킵 → 강한 부정 신호
}

def compute_feedback_reward(feedback_type: str, listen_duration_pct: float) -> float:
    """
    사용자 피드백(스킵/완청/좋아요)으로 보상을 계산합니다.
    이게 RL에서 가장 중요한 보상 신호입니다.

    Args:
        feedback_type: "liked" | "replayed" | "listened" | "skipped"
        listen_duration_pct: 청취 비율 (0~1)

    Returns:
        reward (float), 범위: -1.5 ~ 2.0
    """
    base = FEEDBACK_BASE_REWARDS.get(feedback_type, 0.0)

    if feedback_type == "listened":
        # 완청 보상은 청취 비율에 비례
        # 30% 미만이면 사실상 스킵
        if listen_duration_pct < 0.3:
            return -0.8
        base = base * listen_duration_pct  # 0.24 ~ 0.8

    elif feedback_type == "skipped":
        # 얼마나 빨리 스킵했는지 반영 (바로 스킵 = 더 큰 패널티)
        skip_penalty = -1.5 + listen_duration_pct * 0.5  # -1.5 ~ -1.0
        return max(-1.5, skip_penalty)

    return base

# ── 학습 스텝 ─────────────────────────────────────────────────────────────────
def train_step() -> float | None:
    if len(memory) < BATCH_SIZE:
        return None

    transitions, indices = memory.sample(BATCH_SIZE)

    batch_state      = torch.FloatTensor([t[0] for t in transitions]).to(device)
    batch_action     = torch.LongTensor([t[1] for t in transitions]).view(-1, 1).to(device)
    batch_reward     = torch.FloatTensor([t[2] for t in transitions]).view(-1, 1).to(device)
    batch_next_state = torch.FloatTensor([t[3] for t in transitions]).to(device)
    batch_done       = torch.FloatTensor([t[4] for t in transitions]).view(-1, 1).to(device)

    model.train()
    current_q, _ = model(batch_state)
    current_q_val = current_q.gather(1, batch_action)

    with torch.no_grad():
        next_q, _ = target_model(batch_next_state)
        max_next_q = next_q.max(1)[0].view(-1, 1)
        target_q = batch_reward + (GAMMA * max_next_q * (1 - batch_done))

    td_errors = torch.abs(current_q_val - target_q).detach().cpu().numpy()
    memory.update_priorities(indices, td_errors)

    loss = criterion(current_q_val, target_q)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if total_episodes % TARGET_UPDATE_INTERVAL == 0:
        target_model.load_state_dict(model.state_dict())
        target_model.eval()

    return loss.item()

# ── 서버에서 호출하는 실제 경험 추가 함수 ────────────────────────────────────
def push_experience(state: list, action: int, reward: float,
                    next_state: list, done: bool) -> float | None:
    """
    실제 대화 데이터를 메모리에 저장하고 즉시 학습 스텝을 실행합니다.
    AIServer/server.py에서 호출합니다.

    Returns:
        loss 값 (float) 또는 데이터 부족 시 None
    """
    global total_episodes
    memory.push(state, action, reward, next_state, done)
    total_episodes += 1
    loss = train_step()

    # 100번마다 체크포인트 저장
    if total_episodes % 100 == 0:
        save_checkpoint()
        print(f"💾 체크포인트 저장 완료 (누적: {total_episodes}회)")

    return loss

# ── Spotify 피드백 기반 학습 함수 ─────────────────────────────────────────────
def push_feedback(state: list, action: int, feedback_type: str,
                  listen_duration_pct: float, next_state: list) -> float | None:
    """
    사용자의 Spotify 피드백(스킵/완청/좋아요)으로 RL 학습을 진행합니다.
    /feedback 엔드포인트에서 호출합니다.

    이 함수의 보상 신호가 대화 기반 보상보다 훨씬 직접적이고 강력합니다.

    Args:
        state: 추천 당시의 RL 상태 벡터
        action: 추천 당시 선택한 행동 인덱스
        feedback_type: "liked" | "replayed" | "listened" | "skipped"
        listen_duration_pct: 청취 비율 (0~1)
        next_state: 현재 RL 상태 벡터

    Returns:
        loss 값 또는 None
    """
    reward = compute_feedback_reward(feedback_type, listen_duration_pct)
    loss = push_experience(state, action, reward, next_state, done=False)
    print(f"[Feedback] {feedback_type} (청취 {listen_duration_pct:.0%}) → reward={reward:.2f}")
    return loss

# ── 모델 추론 (서버에서 행동 선택 시 사용) ────────────────────────────────────
def select_action(state: list) -> tuple[int, int]:
    """
    주어진 상태에서 greedy하게 행동을 선택합니다.

    Returns:
        (action_idx, detail_idx)
    """
    model.eval()
    state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
    with torch.no_grad():
        action_scores, detail_scores = model(state_tensor)
        action_idx = int(torch.argmax(action_scores).item())
        detail_idx = int(torch.argmax(detail_scores).item())
    return action_idx, detail_idx

# ── 오프라인 시뮬레이션 학습 ──────────────────────────────────────────────────
def _simulate_state(prev_action: int = 0, turn: int = 0, session_sec: float = 0.0) -> list:
    """현실적인 시뮬레이션 상태 벡터 생성"""
    sentiment = random.uniform(-1.0, 1.0)
    arousal = random.uniform(0.0, 1.0)
    bpm_norm = random.uniform(0.0, 1.0)
    energy = random.uniform(0.0, 1.0)
    danceability = random.uniform(0.0, 1.0)

    # 장르 원핫 (랜덤 하나 선택)
    genre_idx = random.randint(0, 3)
    genre_onehot = [1.0 if i == genre_idx else 0.0 for i in range(4)]

    turns_norm = min(turn / 20.0, 1.0)
    session_time_norm = min(session_sec / 3600.0, 1.0)
    prev_action_norm = prev_action / 3.0

    return [sentiment, arousal, bpm_norm, energy, danceability,
            *genre_onehot, turns_norm, session_time_norm, prev_action_norm]


def start_offline_training(new_episodes: int = 200):
    """시뮬레이션 데이터로 오프라인 사전 학습 실행"""
    global total_episodes
    print(f"\n🚀 오프라인 학습 {new_episodes}회 시작... (현재 누적: {total_episodes})")

    prev_action = 0
    for i in range(new_episodes):
        total_episodes += 1

        state = _simulate_state(prev_action=prev_action, turn=i % 20,
                                session_sec=float(i * 30))
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)

        model.eval()
        with torch.no_grad():
            action_scores, _ = model(state_tensor)
            action = int(torch.argmax(action_scores).item())

        sentiment = state[0]
        reward = compute_reward(sentiment, action)

        next_state = _simulate_state(prev_action=action, turn=(i + 1) % 20,
                                     session_sec=float((i + 1) * 30))
        memory.push(state, action, reward, next_state, False)

        loss_val = train_step()
        prev_action = action

        if total_episodes % 20 == 0:
            status = f"Loss: {loss_val:.4f} 📉" if loss_val else "데이터 수집 중..."
            print(f"  에피소드 {total_episodes:>5} | {status}")
            if loss_val and total_episodes % TARGET_UPDATE_INTERVAL == 0:
                print("  🔄 Target Network 동기화 완료")

    save_checkpoint()
    print(f"\n💾 오프라인 학습 완료 및 저장 (누적: {total_episodes}회)")


# ── 단독 실행 ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 40)
    print("   MasterAgent 오프라인 학습 시작 (v2.0)")
    print("=" * 40)
    load_checkpoint()
    start_offline_training(200)
    print("\n✅ 학습 완료.")
