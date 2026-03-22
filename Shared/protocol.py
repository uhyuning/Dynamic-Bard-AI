# Shared/protocol.py
from pydantic import BaseModel
from typing import Optional

# ── UE5 ↔ AIServer 통신용 ──────────────────────────────────────────────────
class EnvState(BaseModel):
    """언리얼 엔진에서 서버로 보내는 환경 상태"""
    position: list       # [x, y, z]
    velocity: list       # [vx, vy, vz]
    target_dist: float = 0.0

class AIResponse(BaseModel):
    """서버에서 언리얼 엔진으로 보내는 AI 응답"""
    action: list         # [action_idx, detail_idx]
    message: str = ""
    recommended_genre: str = ""

# ── Spotify 트랙 정보 ─────────────────────────────────────────────────────────
class SpotifyTrack(BaseModel):
    """Spotify에서 가져온 실제 트랙 정보"""
    track_id: str                   # Spotify 트랙 ID
    name: str                       # 곡 제목
    artist: str                     # 아티스트
    preview_url: str = ""           # 30초 미리듣기 MP3 URL (무료, UE5에서 직접 재생)
    spotify_uri: str = ""           # spotify:track:xxx (Premium 전체 재생용)
    spotify_url: str = ""           # 웹 플레이어 URL
    # Spotify Audio Features (RL 학습에 사용)
    energy: float = 0.5             # 에너지 (0~1)
    valence: float = 0.5            # 음악 긍정도 (0~1, 높을수록 밝고 긍정적)
    tempo: float = 100.0            # BPM
    danceability: float = 0.5       # 댄서빌리티 (0~1)
    acousticness: float = 0.5       # 어쿠스틱 여부 (0~1)
    mood_label: str = ""            # RL 행동 레이블 (잔잔/신남/감성/집중)

# ── 대화 API용 ───────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    """사용자가 AI에게 보내는 채팅 메시지"""
    message: str

class ChatResponse(BaseModel):
    """AI가 사용자에게 보내는 채팅 응답"""
    reply: str                              # GPT 대화 응답
    sentiment: float                        # 감정 점수 (-1.0: 매우 부정 ~ 1.0: 매우 긍정)
    arousal: float                          # 에너지 수준 (0.0: 차분 ~ 1.0: 매우 활발)
    action_taken: str                       # RL이 선택한 행동 이름
    action_idx: int                         # RL 행동 인덱스 (0~3)
    track: Optional[SpotifyTrack] = None    # 추천 트랙 (Spotify 연동 시 포함)

# ── 사용자 피드백 (RL 학습 핵심) ──────────────────────────────────────────────
class FeedbackMessage(BaseModel):
    """
    사용자가 노래를 들은 후 UE5에서 보내는 피드백.
    이 피드백이 RL의 보상 신호가 됩니다.

    feedback_type 값:
      "liked"    : 좋아요 (+2.0)
      "replayed" : 다시 듣기 (+1.5)
      "listened" : 완청     (+0.5 ~ +1.0, 청취율 반영)
      "skipped"  : 스킵     (-1.5)
    """
    track_id: str
    action_idx: int                         # 이 트랙을 추천한 RL 행동 인덱스
    feedback_type: str                      # "liked" | "replayed" | "listened" | "skipped"
    listen_duration_pct: float = 1.0        # 청취 비율 (0~1, 1.0 = 완청)
