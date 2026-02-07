from fastapi import FastAPI
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__)) # 현재 AIServer 폴더 위치
project_root = os.path.dirname(current_dir)             # 그 위 상위 폴더(Root)

if project_root not in sys.path:
    # insert(0, ...)을 써서 파이썬이 가방 맨 앞칸에서 우리 프로젝트 폴더를 찾게 합니다.
    sys.path.insert(0, project_root)


try:
    from Shared.protocol import EnvState, AIResponse
except ModuleNotFoundError:
    print("❌ 에러: Shared/protocol.py 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
    sys.exit(1)

app = FastAPI()

# 나중에 사용할 연구실 부품들 (준비 완료)
# from RL_Trainer.models.model import DQN 
# from RL_Trainer.memory import ReplayMemory 

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "message": "서버가 정상 작동 중입니다! 🚀",
        "info": "이제 언리얼에서 신호를 보낼 준비가 됐어!"
    }

# 3. 언리얼로부터 데이터를 받아 AI가 판단(Action)을 내리는 곳
@app.post("/act", response_model=AIResponse)
async def get_action(state: EnvState):
    # [로그 확인] 하윤이가 언리얼에서 보낸 데이터가 서버 터미널에 찍힙니다.
    print(f"📍 [수신] 위치: {state.position} | 🎯 목표 거리: {state.target_dist}")

    # TODO: 나중에 여기에 RL_Trainer의 모델을 연결하여 실제 판단 로직을 넣습니다.
    # 예: action = model.predict(state)
    
    # [테스트용] 지금은 일단 '전진' 신호(1.0, 0.0)를 반환합니다.
    test_action = [1.0, 0.0] 
    
    return AIResponse(
        action=test_action, 
        message="서버가 데이터를 확인하고 행동을 결정했습니다."
    )

if __name__ == "__main__":
    import uvicorn
    # host="0.0.0.0"은 같은 네트워크 내의 다른 장치에서도 접속을 허용합니다.
    print("💡 서버를 시작합니다. 언리얼 프로젝트에서 http://localhost:8000 으로 접속하세요.")
    uvicorn.run(app, host="0.0.0.0", port=8000)