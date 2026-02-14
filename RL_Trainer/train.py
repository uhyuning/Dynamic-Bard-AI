import torch
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
import random
import os
import numpy as np # [추가] 수치 계산용

from models.model import MasterAgent  
# [수정] 일반 ReplayMemory에서 PrioritizedMemory로 교체
from memory import PrioritizedMemory       

# 1. 하이퍼파라미터
STATE_DIM = 16  
ACTION_DIM = 4  
BATCH_SIZE = 32 
LR = 0.001      
GAMMA = 0.99    
SAVE_PATH = "master_agent_brain.pth"
TARGET_UPDATE_INTERVAL = 100 

# 2. 인스턴스 생성
model = MasterAgent(STATE_DIM, ACTION_DIM)
target_model = MasterAgent(STATE_DIM, ACTION_DIM)
target_model.load_state_dict(model.state_dict())

# [수정] 우선순위 메모리로 인스턴스화
memory = PrioritizedMemory(capacity=10000)
optimizer = optim.Adam(model.parameters(), lr=LR)
criterion = nn.MSELoss() 

total_episodes = 0 

if os.path.exists(SAVE_PATH):
    checkpoint = torch.load(SAVE_PATH)
    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
        target_model.load_state_dict(checkpoint['model_state_dict'])
        total_episodes = checkpoint.get('total_episodes', 0)
    else:
        model.load_state_dict(checkpoint)
        target_model.load_state_dict(checkpoint)
    print(f"📜 기존 지능을 불러왔습니다. (누적 학습 횟수: {total_episodes}회)")
else:
    print("🐣 새로운 지능으로 처음부터 시작합니다.")

def give_reward(action, user_sentiment):
    reward = 0.0
    if action == 1 and user_sentiment == "sad":
        reward = 1.0
    return reward

def train_step():
    if len(memory) < BATCH_SIZE:
        return None
    
    # [수정] 샘플링 시 인덱스(indices)를 함께 받아옵니다.
    transitions, indices = memory.sample(BATCH_SIZE)
    
    batch_state = torch.FloatTensor([t[0] for t in transitions])
    batch_action = torch.LongTensor([t[1] for t in transitions]).view(-1, 1)
    batch_reward = torch.FloatTensor([t[2] for t in transitions]).view(-1, 1)
    batch_next_state = torch.FloatTensor([t[3] for t in transitions])
    batch_done = torch.FloatTensor([t[4] for t in transitions]).view(-1, 1)
    
    current_q, _ = model(batch_state)
    current_q_val = current_q.gather(1, batch_action)
    
    with torch.no_grad():
        next_q, _ = target_model(batch_next_state)
        max_next_q = next_q.max(1)[0].view(-1, 1)
        target_q = batch_reward + (GAMMA * max_next_q * (1 - batch_done))
    
    # [핵심 추가] 각 데이터의 오차(TD-Error) 계산
    # 이 오차가 클수록 AI가 "오! 이건 몰랐는데?" 하고 중요하게 여깁니다.
    td_errors = torch.abs(current_q_val - target_q).detach().cpu().numpy()
    
    # [수정] 메모리에 실제 학습 오차를 반영하여 우선순위 업데이트
    memory.update_priorities(indices, td_errors)
    
    loss = criterion(current_q_val, target_q)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    if total_episodes % TARGET_UPDATE_INTERVAL == 0:
        target_model.load_state_dict(model.state_dict())
        
    return loss.item()

def start_real_training(new_episodes=100):
    global total_episodes 
    print(f"\n🚀 추가 학습 {new_episodes}회를 시작합니다... (현재 누적: {total_episodes})")
    
    for i in range(new_episodes):
        total_episodes += 1 
        
        state = [random.uniform(-1, 1) for _ in range(STATE_DIM)] 
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            action_scores, _ = model(state_tensor)
            action = torch.argmax(action_scores).item()
        
        user_sentiment = "sad" if state[0] < 0 else "happy"
        reward = give_reward(action, user_sentiment)
        
        # [수정] 이제 메모리가 우선순위를 관리합니다.
        memory.push(state, action, reward, state, False)
        
        loss_val = train_step()
        
        if total_episodes % 10 == 0:
            if loss_val:
                print(f"에피소드 {total_episodes} | Loss: {loss_val:.4f} 📉")
                if total_episodes % TARGET_UPDATE_INTERVAL == 0:
                    print("🔄 [System] Target Network Synchronized.")
            else:
                print(f"에피소드 {total_episodes} | 데이터 수집 중...")

    save_data = {
        'model_state_dict': model.state_dict(),
        'total_episodes': total_episodes
    }
    torch.save(save_data, SAVE_PATH)
    print(f"\n💾 지능과 카운트가 저장되었습니다. (누적: {total_episodes}회)")

if __name__ == "__main__":
    print("================================")
    print("   AI 시스템 연결 성공! (v1.5)   ")
    print("================================")
    
    start_real_training(100) 
    print("\n✅ 모든 과정이 종료되었습니다.")