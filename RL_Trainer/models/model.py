import torch
import torch.nn as nn

# ── 상태 벡터 정의 (STATE_DIM = 12) ──────────────────────────────────────────
# [0]  sentiment_score   : GPT 감정 분석 점수  (-1.0 ~ 1.0)
# [1]  arousal_level     : 사용자 에너지 수준   (0.0 ~ 1.0)
# [2]  bpm_norm          : 현재 음악 BPM / 160  (0.0 ~ 1.0)
# [3]  music_energy      : 음악 에너지           (0.0 ~ 1.0)
# [4]  music_valence     : 음악 긍정도 (Spotify valence) (0.0 ~ 1.0)
# [5]  genre_kpop        : K-Pop 여부            (0 or 1)
# [6]  genre_lofi        : Lo-fi 여부            (0 or 1)
# [7]  genre_hiphop      : Hip-hop 여부          (0 or 1)
# [8]  genre_classical   : Classical 여부        (0 or 1)
# [9]  turns_norm        : 대화 턴 수 / 20       (0.0 ~ 1.0)
# [10] session_time_norm : 세션 경과 시간 / 3600  (0.0 ~ 1.0)
# [11] prev_action_norm  : 이전 행동 인덱스 / 3   (0.0 ~ 1.0)

# ── 행동 정의 (ACTION_DIM = 4) ───────────────────────────────────────────────
# 0: 잔잔한 음악 추천 (Lo-fi)
# 1: 신나는 음악 추천 (K-Pop)
# 2: 감성적인 음악 추천 (Hip-hop / Ballad)
# 3: 집중용 음악 추천 (Classical)

STATE_DIM = 12
ACTION_DIM = 4


class MasterAgent(nn.Module):
    def __init__(self, state_dim=STATE_DIM, action_dim=ACTION_DIM):
        super(MasterAgent, self).__init__()

        # 공통 상황 이해 레이어 (두뇌 중심부)
        self.shared_layer = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU()
        )

        # 행동 선택 헤드: 0=잔잔 / 1=신남 / 2=감성 / 3=집중
        self.action_head = nn.Linear(256, action_dim)

        # 세부 옵션 헤드: 구체적인 곡 선택 등 (10가지 세부 옵션)
        self.detail_head = nn.Linear(256, 10)

    def forward(self, x):
        context = self.shared_layer(x)
        action_scores = self.action_head(context)
        detail_scores = self.detail_head(context)
        return action_scores, detail_scores
