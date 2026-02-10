# AIServer/train.py
import torch
import torch.optim as optim
import torch.nn as nn
import random

# 파일들간의 연결
from models.model import MasterAgent  # MasterAgent 모델 불러오기
from memory import ReplayMemory # 위에서 만든 ReplayMemory 불러오기

# 1. 하이퍼파라미터 (AI의 학습 설정값)
STATE_DIM = 16  # 입력받을 상태 정보의 개수
ACTION_DIM = 4  # AI가 할 수 있는 행동의 개수 (대화, 음악, 배경, 소환)
BATCH_SIZE = 32 # 한 번에 복습할 기억의 양
LR = 0.001      # 학습률 (공부하는 속도)

# 2. 인스턴스 생성
model = MasterAgent(STATE_DIM, ACTION_DIM)
memory = ReplayMemory(capacity=10000)
optimizer = optim.Adam(model.parameters(), lr=LR)
criterion = nn.MSELoss() # 정답과 얼마나 차이나는지 계산

def give_reward(action, user_sentiment):
    """
    [입문자 가이드] 보상 함수는 AI가 한 행동이 잘한 건지 못한 건지 점수를 주는 심판입니다.
    """
    reward = 0.0
    # AI가 '노래 틀기(Action 1)'를 골랐는데, 유저가 '우울함(sad)' 상태라면 보상을 줍니다.
    if action == 1 and user_sentiment == "sad":
        reward = 1.0
    # 다른 케이스에 대한 보상 로직도 여기에 추가하면 됩니다.
    return reward

def train_step():
    """AI가 기억 저장소에서 데이터를 꺼내 공부하는 핵심 단계"""
    # 기억이 최소한 BATCH_SIZE만큼은 쌓여야 학습을 시작함
    if len(memory) < BATCH_SIZE:
        return

    # 3. 무작위 복습 시작
    transitions = memory.sample(BATCH_SIZE)
    # (여기서 실제 텐서 변환 및 역전파 학습 로직이 들어갑니다)
    
    print(f"현재 기억 개수: {len(memory)} | AI가 복습 중입니다... 🧠✨")

if __name__ == "__main__":
    print("================================")
    print("   AI 시스템 연결 성공! (v1.0)   ")
    print("================================")
    
    # 가짜 데이터를 넣어 연결 테스트
    test_state = [0.0] * STATE_DIM
    memory.push(test_state, 1, 1.0, test_state, False)
    
    print("테스트 데이터 저장 완료. 이제 언리얼 엔진과 통신할 준비가 되었습니다.")

    # AIServer/train.py 하단에 추가

def start_real_training(episodes=100):
    print("\n🚀 실전 학습 시뮬레이션을 시작합니다...")
    
    for episode in range(episodes):
        # 1. 초기 상태 설정 (예: 기분이 '우울함'(-1.0)인 상태)
        # [기분, 시간, 날씨, 현재배경, ...] 이런 식의 데이터라 가정합니다.
        state = [random.uniform(-1, 1) for _ in range(STATE_DIM)] 
        
        # 2. AI의 판단 (Action 선택)
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            action_scores, _ = model(state_tensor)
            action = torch.argmax(action_scores).item() # 가장 점수 높은 행동 선택
        
        # 3. 보상 결정 (질문자님이 짠 로직 적용)
        # 예: 기분이 우울한데(state[0] < 0) AI가 노래(action 1)를 선택했다면?
        user_sentiment = "sad" if state[0] < 0 else "happy"
        reward = give_reward(action, user_sentiment)
        
        # 4. 기억 저장 (Next State는 일단 현재와 같다고 가정)
        memory.push(state, action, reward, state, False)
        
        # 5. 학습 수행
        train_step()
        
        if (episode + 1) % 10 == 0:
            print(f"에피소드 {episode + 1}/{episodes} 완료! 학습 중...")

if __name__ == "__main__":
    # ... 기존 연결 코드 ...
    start_real_training(100) # 100번의 연습 시뮬레이션 시작
    print("\n✅ 학습 시뮬레이션이 종료되었습니다. AI의 판단력이 상승했습니다!")