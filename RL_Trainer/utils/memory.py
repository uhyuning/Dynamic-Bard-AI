import collections
import random

class ReplayBuffer:
    """
    과거에 어떤 음악(상태)에서 어떻게 움직였고(행동), 
    점수를 얼마 받았는지(보상)를 저장해두었다가 나중에 꺼내서 공부합니다.
    """
    def __init__(self, capacity=10000):
        # capacity: 메모리 장치의 최대 크기 (너무 옛날 기억은 지워요)
        self.buffer = collections.deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        """새로운 경험을 메모리에 저장합니다."""
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        """저장된 기억들 중 무작위로 몇 개를 꺼내서 복습합니다."""
        # 무작위로 꺼내야 특정 상황에만 치우치지 않고 골고루 배울 수 있어요!
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        """현재 기억이 몇 개나 쌓였는지 확인합니다."""
        return len(self.buffer)