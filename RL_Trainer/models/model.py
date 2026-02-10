import torch
import torch.nn as nn
import torch.nn.functional as F

class MasterAgent(nn.Module):
    def __init__(self, state_dim=16, action_dim=4): # 상태와 행동의 가짓수를 늘렸어요.
        super(MasterAgent, self).__init__()
        
        # 공통적인 상황 이해 (두뇌의 중심부)
        self.shared_layer = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU()
        )
        
        # 가짓수 선택 (어떤 종류의 행동을 할 것인가?)
        # 0: 대화, 1: 음악, 2: 배경, 3: 소환
        self.action_head = nn.Linear(256, action_dim)
        
        # 세부 판단 (어떤 노래? 어떤 악기? - 텍스트/카테고리 분류용)
        self.detail_head = nn.Linear(256, 10) # 10가지 세부 옵션 중 선택

    def forward(self, x):
        # 1. 상황을 공통적으로 분석합니다.
        context = self.shared_layer(x)
        
        # 2. 어떤 '종류'의 행동을 할지 점수를 매깁니다.
        action_scores = self.action_head(context)
        
        # 3. 그 행동 내에서 어떤 '세부 옵션'이 좋을지 점수를 매깁니다.
        detail_scores = self.detail_head(context)
        
        return action_scores, detail_scores