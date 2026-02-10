# AIServer/memory.py
from collections import deque
import random

class ReplayMemory:
    def __init__(self, capacity=10000):
        # deque는 설정한 용량(capacity)이 넘어가면 가장 오래된 기억을 자동으로 지워줍니다.
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        # AI의 경험을 튜플 형태로 저장함
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        # 학습할 때 기억들 중에서 batch_size만큼 무작위로 꺼내옴 (편향 방지)
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        # 현재 기억이 몇 개 쌓였는지 반환함
        return len(self.buffer)