import torch
import torch.nn as nn
import torch.nn.functional as F

class DQN(nn.Module):
    """
    [입문자 가이드] DQN(Deep Q-Network)은 AI의 '뇌'에 해당합니다.
    언리얼로부터 상태(State)를 입력받아, 어떤 행동(Action)이 가장 좋을지 점수를 매깁니다.
    """
    def __init__(self, state_dim=8, action_dim=2):
        super(DQN, self).__init__()
        # 입력층 -> 은닉층 1 (128개의 뉴런)
        self.fc1 = nn.Linear(state_dim, 128)
        # 은닉층 1 -> 은닉층 2 (128개의 뉴런)
        self.fc2 = nn.Linear(128, 128)
        # 은닉층 2 -> 출력층 (행동의 개수만큼 점수 출력)
        self.fc3 = nn.Linear(128, action_dim)

    def forward(self, x):
        # ReLU는 인공 뉴런의 활성화를 조절하는 '스위치' 같은 역할입니다.
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)