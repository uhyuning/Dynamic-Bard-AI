"""
AIServer/server.py — 메인 AI 서버 (v3.0 - Spotify 실제 연동)

[엔드포인트]
  GET  /             → 서버 상태 + Spotify 연결 상태
  POST /chat         → 사용자 채팅 → GPT 감정 분석 → RL → Spotify 실제 곡 추천
  POST /feedback     → 사용자 피드백 (스킵/완청/좋아요) → RL 학습 핵심 보상
  GET  /now-playing  → 현재 Spotify 재생 중 트랙 정보
  GET  /history      → 최근 재생 목록 (RL 히스토리)
  GET  /status       → RL 학습 현황
  POST /act          → 언리얼 엔진용 행동 결정 (UE5 연동)

[흐름 - Spotify 연동 버전]
  사용자 메시지
    → GPT (응답 + 감정/에너지 수치화)
    → RL 상태 구성 (12차원, Spotify 실제 audio features 포함)
    → MasterAgent → mood 방향 결정 (0~3)
    → Spotify API → 해당 mood에 맞는 실제 곡 검색
    → UE5로 preview_url / spotify_uri 전달
    → 사용자가 노래 들음
    → POST /feedback (스킵/완청/좋아요)
    → RL 강한 보상 신호로 학습
"""

import sys
import os
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException
from Shared.protocol import (
    EnvState, AIResponse, ChatMessage, ChatResponse,
    SpotifyTrack, FeedbackMessage
)

trainer_dir = os.path.join(project_root, "RL_Trainer")
if trainer_dir not in sys.path:
    sys.path.insert(0, trainer_dir)

from RL_Trainer.train import (
    load_checkpoint, push_experience, push_feedback, select_action,
    compute_reward, compute_feedback_reward,
    ACTION_NAMES, ACTION_GENRE, SAVE_PATH, STATE_DIM, ACTION_DIM
)
import RL_Trainer.train as trainer

from spotify_client import SpotifyController
from gpt_client import GPTController

# ── 앱 초기화 ────────────────────────────────────────────────────────────────
app = FastAPI(title="Dynamic Bard AI Server", version="3.0")

spotify = SpotifyController()   # 실제 Spotify (실패 시 Mock 자동 전환)
gpt = GPTController()

# ── 세션 상태 ─────────────────────────────────────────────────────────────────
session = {
    "prev_state": None,
    "prev_action": 0,
    "prev_sentiment": 0.0,
    "prev_track_id": None,             # 이전에 추천한 트랙 ID (피드백 매칭용)
    "prev_track_state": None,          # 이전 트랙 추천 당시 RL 상태 (피드백 학습용)
    "conversation_turns": 0,
    "session_start": time.time(),
    "total_reward": 0.0,
    "current_track": None,             # 현재 추천된 SpotifyTrack 정보
}

load_checkpoint()


# ── 상태 벡터 구성 ─────────────────────────────────────────────────────────────
def _build_state(sentiment: float, arousal: float, track: dict,
                 turns: int, session_sec: float, prev_action: int) -> list:
    """
    12차원 RL 상태 벡터.

    [0]  sentiment_score     (-1~1)        GPT 분석 사용자 감정
    [1]  arousal_level       (0~1)         GPT 분석 사용자 에너지
    [2]  bpm_norm            (tempo/160)   Spotify 실제 BPM
    [3]  music_energy        (0~1)         Spotify 실제 에너지
    [4]  music_valence       (0~1)         Spotify 실제 긍정도 (핵심!)
    [5]  genre_calm          (0 or 1)      action=0 (잔잔)
    [6]  genre_upbeat        (0 or 1)      action=1 (신남)
    [7]  genre_emotional     (0 or 1)      action=2 (감성)
    [8]  genre_focus         (0 or 1)      action=3 (집중)
    [9]  turns_norm          (turns/20)
    [10] session_time_norm   (sec/3600)
    [11] prev_action_norm    (action/3)
    """
    # 장르 원핫: 이전 행동(mood 방향)으로 인코딩
    genre_onehot = [0.0] * 4
    if 0 <= prev_action < 4:
        genre_onehot[prev_action] = 1.0

    return [
        float(sentiment),
        float(arousal),
        float(track.get("tempo", 100.0) / 160.0),
        float(track.get("energy", 0.5)),
        float(track.get("valence", 0.5)),        # danceability → valence 로 변경
        *genre_onehot,
        min(float(turns) / 20.0, 1.0),
        min(float(session_sec) / 3600.0, 1.0),
        float(prev_action) / 3.0,
    ]


def _track_dict_to_model(track: dict) -> SpotifyTrack:
    """spotify_client의 dict를 SpotifyTrack 모델로 변환"""
    return SpotifyTrack(
        track_id=track.get("track_id", ""),
        name=track.get("name", "Unknown"),
        artist=track.get("artist", "Unknown"),
        preview_url=track.get("preview_url", ""),
        spotify_uri=track.get("spotify_uri", ""),
        spotify_url=track.get("spotify_url", ""),
        energy=round(track.get("energy", 0.5), 3),
        valence=round(track.get("valence", 0.5), 3),
        tempo=round(track.get("tempo", 100.0), 1),
        danceability=round(track.get("danceability", 0.5), 3),
        acousticness=round(track.get("acousticness", 0.5), 3),
        mood_label=track.get("mood_label", ""),
    )


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {
        "status": "online",
        "version": "3.0",
        "spotify_connected": spotify.is_connected(),
        "spotify_mode": "real" if spotify.is_connected() else "mock",
        "endpoints": ["/chat", "/feedback", "/now-playing", "/history", "/status", "/act"],
    }


@app.get("/status")
def get_status():
    return {
        "total_episodes": trainer.total_episodes,
        "memory_size": len(trainer.memory),
        "session_turns": session["conversation_turns"],
        "total_reward_this_session": round(session["total_reward"], 3),
        "spotify_connected": spotify.is_connected(),
        "current_track": session["current_track"],
        "checkpoint_exists": os.path.exists(SAVE_PATH),
    }


@app.get("/now-playing")
def now_playing():
    """현재 Spotify에서 재생 중인 트랙 정보"""
    track = spotify.get_current_track()
    if not track:
        return {"playing": False, "track": None}
    return {"playing": True, "track": track}


@app.get("/history")
def get_history():
    """최근 Spotify 재생 목록 (RL 학습 히스토리 분석용)"""
    tracks = spotify.get_recently_played(limit=20)
    return {"count": len(tracks), "tracks": tracks}


@app.post("/chat", response_model=ChatResponse)
async def chat(msg: ChatMessage):
    """
    사용자 채팅 메시지 처리:
    1. GPT → 대화 응답 + 감정/에너지 분석
    2. RL → mood 방향 결정 (0~3)
    3. Spotify → 해당 mood의 실제 곡 추천
    4. 대화 기반 보상으로 RL 학습 (가벼운 신호)
    5. 응답 + 트랙 정보 반환
    """
    session_sec = time.time() - session["session_start"]

    # [1] GPT 분석
    gpt_result = gpt.analyze_and_reply(
        user_message=msg.message,
        current_genre=session.get("current_genre", ""),
        current_bpm=session.get("current_bpm", 100.0),
    )
    sentiment: float = gpt_result["sentiment"]
    arousal: float   = gpt_result["arousal"]
    reply: str       = gpt_result["reply"]

    # [2] 임시 상태 벡터 구성 (Spotify 결과 반영 전)
    tmp_track = {"tempo": 100.0, "energy": 0.5, "valence": 0.5}
    current_state = _build_state(
        sentiment=sentiment, arousal=arousal, track=tmp_track,
        turns=session["conversation_turns"],
        session_sec=session_sec,
        prev_action=session["prev_action"]
    )

    # [3] RL → mood 행동 선택
    action_idx, _ = select_action(current_state)
    action_name   = ACTION_NAMES[action_idx]

    # [4] Spotify → 실제 곡 추천 (상위 1곡)
    tracks = spotify.get_recommendations_for_action(
        action_idx=action_idx,
        sentiment=sentiment,
        limit=3,
    )
    chosen_track_dict = tracks[0] if tracks else None
    chosen_track      = _track_dict_to_model(chosen_track_dict) if chosen_track_dict else None

    # [5] 실제 트랙 audio features로 상태 재구성
    real_track_data = chosen_track_dict if chosen_track_dict else tmp_track
    current_state = _build_state(
        sentiment=sentiment, arousal=arousal, track=real_track_data,
        turns=session["conversation_turns"],
        session_sec=session_sec,
        prev_action=session["prev_action"]
    )

    # [6] 이전 대화 기반 보상 계산 + 학습 (가벼운 신호)
    if session["prev_state"] is not None:
        mood_improvement = sentiment - session["prev_sentiment"]
        action_reward = compute_reward(session["prev_sentiment"], session["prev_action"])
        reward = action_reward + mood_improvement * 0.3
        reward = max(-1.5, min(1.5, reward))

        loss = push_experience(
            state=session["prev_state"],
            action=session["prev_action"],
            reward=reward,
            next_state=current_state,
            done=False,
        )
        session["total_reward"] += reward
        if loss is not None:
            print(f"[RL/Chat] Loss={loss:.4f} Reward={reward:+.2f} Episode={trainer.total_episodes}")

    # [7] 세션 업데이트
    session["prev_state"]       = current_state
    session["prev_action"]      = action_idx
    session["prev_sentiment"]   = sentiment
    session["prev_track_id"]    = chosen_track.track_id if chosen_track else None
    session["prev_track_state"] = current_state
    session["current_track"]    = chosen_track.model_dump() if chosen_track else None
    session["current_genre"]    = real_track_data.get("genre", "")
    session["current_bpm"]      = real_track_data.get("tempo", 100.0)
    session["conversation_turns"] += 1

    print(f"\n[Chat Turn {session['conversation_turns']}]")
    print(f"  User   : {msg.message[:60]}")
    print(f"  GPT    : sentiment={sentiment:+.2f} arousal={arousal:.2f}")
    print(f"  RL     : action={action_idx} ({action_name})")
    if chosen_track:
        print(f"  Spotify: {chosen_track.name} - {chosen_track.artist}")
        print(f"           energy={chosen_track.energy:.2f} valence={chosen_track.valence:.2f} tempo={chosen_track.tempo:.0f}BPM")

    return ChatResponse(
        reply=reply,
        sentiment=round(sentiment, 3),
        arousal=round(arousal, 3),
        action_taken=action_name,
        action_idx=action_idx,
        track=chosen_track,
    )


@app.post("/feedback")
async def feedback(fb: FeedbackMessage):
    """
    사용자가 노래를 들은 후 보내는 피드백.
    이것이 RL의 핵심 학습 신호입니다.

    UE5 또는 앱에서 다음 상황에 자동으로 호출해야 합니다:
      - 노래 스킵 시      → feedback_type="skipped"
      - 노래 완청 시      → feedback_type="listened", listen_duration_pct=1.0
      - 좋아요 버튼 클릭  → feedback_type="liked"
      - 다시 듣기 클릭    → feedback_type="replayed"
    """
    if not session["prev_track_state"]:
        raise HTTPException(status_code=400, detail="피드백을 처리할 이전 트랙 상태가 없습니다.")

    # 현재 임시 상태 (피드백 시점의 next_state)
    session_sec = time.time() - session["session_start"]
    tmp_track   = {"tempo": 100.0, "energy": 0.5, "valence": 0.5}
    next_state  = _build_state(
        sentiment=session["prev_sentiment"], arousal=0.5, track=tmp_track,
        turns=session["conversation_turns"],
        session_sec=session_sec,
        prev_action=session["prev_action"],
    )

    loss = push_feedback(
        state=session["prev_track_state"],
        action=fb.action_idx,
        feedback_type=fb.feedback_type,
        listen_duration_pct=fb.listen_duration_pct,
        next_state=next_state,
    )

    reward = compute_feedback_reward(fb.feedback_type, fb.listen_duration_pct)
    session["total_reward"] += reward

    print(f"[Feedback] track={fb.track_id} type={fb.feedback_type} "
          f"dur={fb.listen_duration_pct:.0%} reward={reward:+.2f} loss={loss}")

    return {
        "received": True,
        "feedback_type": fb.feedback_type,
        "reward": round(reward, 3),
        "total_episodes": trainer.total_episodes,
        "loss": round(loss, 5) if loss else None,
    }


@app.post("/act", response_model=AIResponse)
async def get_action(state: EnvState):
    """언리얼 엔진용 행동 결정 엔드포인트 (UE5 연동)"""
    pos_norm  = sum(abs(p) for p in state.position[:3]) / 3.0
    vel_norm  = sum(abs(v) for v in state.velocity[:3]) / 3.0
    sentiment = max(-1.0, min(1.0, pos_norm - 0.5))
    arousal   = min(1.0, vel_norm)

    tmp_track     = {"tempo": 100.0, "energy": 0.5, "valence": 0.5}
    current_state = _build_state(
        sentiment=sentiment, arousal=arousal, track=tmp_track,
        turns=session["conversation_turns"],
        session_sec=time.time() - session["session_start"],
        prev_action=session["prev_action"],
    )

    action_idx, detail_idx = select_action(current_state)
    action_name = ACTION_NAMES[action_idx]
    genre       = ACTION_GENRE[action_idx]

    return AIResponse(
        action=[float(action_idx), float(detail_idx)],
        message=action_name,
        recommended_genre=genre,
    )


if __name__ == "__main__":
    import uvicorn
    print("Dynamic Bard AI Server v3.0 시작!")
    print(f"Spotify 모드: {'실제 연동' if spotify.is_connected() else 'Mock'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
