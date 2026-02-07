import sys
import os
from fastapi import FastAPI
import torch
import torch.optim as optim
import torch.nn.functional as F

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 부품 가져오기
try:
    from Shared.protocol import EnvState, AIResponse
    from RL_Trainer.models.model import DQN  
    from RL_Trainer.utils.memory import ReplayBuffer
    from spotify_mock import SpotifyMock
    from gpt_client import GPTController
except ModuleNotFoundError as e:
    print(f"❌ 모듈 로드 에러: {e}. 폴더 구조를 확인하세요!")
    sys.exit(1)

app = FastAPI()

# 2. AI 세팅 (뇌, 최적화 도구, 기억 저장소)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DQN(state_dim=8, action_dim=2).to(device)
optimizer = optim.Adam(model.parameters(), lr=0.001)
memory = ReplayBuffer(capacity=10000)

# 3. 감각 및 소통 도구 세팅
spotify = SpotifyMock()
gpt = GPTController()

# [학습용 전역 변수]
last_state = None
last_action = None

@app.get("/")
def read_root():
    return {"status": "online", "message": "종합 AI 연구소 가동 중! 🧠🎶💬"}

@app.post("/act", response_model=AIResponse)
async def get_action(state: EnvState):
    global last_state, last_action
    
    # [1] 현재 음악 정보 가져오기
    music = spotify.get_current_track_info()
    
    # [2] 데이터 정리 (에러 방지를 위해 모든 데이터를 float 숫자로 강제 변환)
    # 위치(3) + 속도(3, 일단 0) + 음악(2) = 총 8개
    try:
        current_state_list = [
            float(state.position[0]), float(state.position[1]), float(state.position[2]),
            0.0, 0.0, 0.0,
            float(music['bpm'] / 160.0),
            float(music['energy'])
        ]
    except Exception as e:
        print(f"⚠️ 데이터 변환 에러: {e}")
        current_state_list = [0.0] * 8

    # [3] 강화학습 - 이전 행동 복습하기
    if last_state is not None:
        reward = 1.0 if (music['energy'] > 0.5 and last_action == 0) else -0.1
        memory.push(last_state, last_action, reward, current_state_list, False)
        
        if len(memory) > 32:
            # 실시간 학습은 여기서 발생 (나중에 학습 알고리즘을 구체화할 수 있습니다)
            pass

    # [4] AI의 현재 행동 결정
    # 리스트를 텐서로 바꿀 때 [ ]로 한 번 더 감싸서 (1, 8) 모양으로 만듭니다.
    input_tensor = torch.tensor([current_state_list], dtype=torch.float32).to(device)
    
    model.eval() # 판단 모드
    with torch.no_grad():
        prediction = model(input_tensor)
        action_idx = int(torch.argmax(prediction).item())

    # 다음 차례를 위해 저장
    last_state = current_state_list
    last_action = action_idx

    # [5] 행동 이름 및 GPT 코멘트 생성
    action_name = "신나게 전진" if action_idx == 0 else "우아하게 회전"
    ai_speech = gpt.get_ai_comment(music['genre'], music['bpm'], action_name)

    # 로그 출력
    print(f"\n[AI 연구소 로그]")
    print(f"🎵 음악: {music['genre']} ({music['bpm']} BPM)")
    print(f"🤖 판단: {action_name}")
    print(f"💬 GPT: {ai_speech}")
    
    # [언리얼로 최종 응답 전송]
    return AIResponse(
        action=[float(action_idx), 0.0], 
        message=str(ai_speech)
    )

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 [최종 수정 완료] AI 서버가 하윤이를 기다립니다!")
    uvicorn.run(app, host="0.0.0.0", port=8000)