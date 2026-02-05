# AIServer/memory.py
from collections import deque
import random

class ReplayMemory:
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        # AI의 경험(상태, 행동, 보상 등)을 저장함
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        # 학습할 때 무작위로 경험을 꺼내옴
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)