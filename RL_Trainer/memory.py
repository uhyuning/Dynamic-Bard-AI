import numpy as np
import random

class PrioritizedMemory:
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.priorities = [] # 데이터의 '중요도'를 저장하는 리스트

    def push(self, state, action, reward, next_state, done):
        # 새로운 기억은 일단 가장 높은 우선순위로 저장 (최소 한 번은 학습 기회 제공)
        max_prio = max(self.priorities) if self.memory else 1.0
        
        if len(self.memory) < self.capacity:
            self.memory.append((state, action, reward, next_state, done))
            self.priorities.append(max_prio)
        else:
            # 오래된 기억부터 삭제 (FIFO 방식)
            self.memory.pop(0)
            self.priorities.pop(0)
            self.memory.append((state, action, reward, next_state, done))
            self.priorities.append(max_prio)

    def sample(self, batch_size):
        if len(self.memory) == 0:
            return [], []
        
        # [핵심] 우선순위에 따라 확률 분포 생성
        prios = np.array(self.priorities, dtype=np.float32)
        probs = prios / prios.sum()
        
        # 확률(p=probs)에 따라 인덱스 선택
        indices = np.random.choice(len(self.memory), batch_size, p=probs)
        samples = [self.memory[idx] for idx in indices]
        
        return samples, indices

    def update_priorities(self, indices, errors):
        # [수정 포인트] errors가 텐서나 배열일 경우를 대비해 flatten()과 float() 처리를 추가
        # 'abs(error)'를 통해 오차의 크기를 중요도로 사용합니다.
        for idx, error in zip(indices, errors.flatten()):
            self.priorities[idx] = float(abs(error)) + 1e-5 

    def __len__(self):
        return len(self.memory)