import torch
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
import random
import os

from models.model import MasterAgent  
from memory import ReplayMemory       

# 1. 하이퍼파라미터
STATE_DIM = 16  
ACTION_DIM = 4  
BATCH_SIZE = 32 
LR = 0.001      
GAMMA = 0.99    
SAVE_PATH = "master_agent_brain.pth"
TARGET_UPDATE_INTERVAL = 100 # [추가] 100번 학습마다 정답지 뇌를 동기화

# 2. 인스턴스 생성
model = MasterAgent(STATE_DIM, ACTION_DIM)
target_model = MasterAgent(STATE_DIM, ACTION_DIM) # [추가] 정답지 전용 뇌 생성
target_model.load_state_dict(model.state_dict()) # 실제 뇌와 똑같이 초기화

memory = ReplayMemory(capacity=10000)
optimizer = optim.Adam(model.parameters(), lr=LR)
criterion = nn.MSELoss() 

total_episodes = 0 

if os.path.exists(SAVE_PATH):
    checkpoint = torch.load(SAVE_PATH)
    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
        target_model.load_state_dict(checkpoint['model_state_dict']) # [추가] 타겟 뇌도 같이 업데이트
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
    transitions = memory.sample(BATCH_SIZE)
    batch_state = torch.FloatTensor([t[0] for t in transitions])
    batch_action = torch.LongTensor([t[1] for t in transitions]).view(-1, 1)
    batch_reward = torch.FloatTensor([t[2] for t in transitions]).view(-1, 1)
    batch_next_state = torch.FloatTensor([t[3] for t in transitions])
    batch_done = torch.FloatTensor([t[4] for t in transitions]).view(-1, 1)
    
    current_q, _ = model(batch_state)
    current_q = current_q.gather(1, batch_action)
    
    with torch.no_grad():
        # [수정] 다음 상태의 가치는 target_model(정답지 뇌)에서 가져옵니다.
        next_q, _ = target_model(batch_next_state)
        max_next_q = next_q.max(1)[0].view(-1, 1)
        target_q = batch_reward + (GAMMA * max_next_q * (1 - batch_done))
    
    loss = criterion(current_q, target_q)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    # [추가] 주기적으로 정답지 뇌 업데이트
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
    print("   AI 시스템 연결 성공! (v1.4)   ")
    print("================================")
    
    start_real_training(100) 
    print("\n✅ 모든 과정이 종료되었습니다.")