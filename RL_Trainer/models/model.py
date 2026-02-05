# RL_Trainer/models/model.py

class DQN:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        # 나중에 여기에 PyTorch나 TensorFlow 신경망이 들어갑니다.
        print(f"뇌 세포 생성 완료! (입력: {state_size}, 출력: {action_size})")

    def forward(self, x):
        # 데이터가 뇌를 통과하며 판단을 내리는 과정
        pass