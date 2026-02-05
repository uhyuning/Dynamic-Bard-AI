# AIServer/server.py
from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os

# [입문자 가이드] 프로젝트 최상위 경로를 시스템 경로에 추가합니다.
# 이렇게 해야 AIServer 폴더 밖의 RL_Trainer나 Shared 폴더를 불러올 수 있음
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# 나중에 사용할 연구실 부품들 미리 주석으로 준비해두기
# from RL_Trainer.models.model import DQN  # AI의 뇌
# from RL_Trainer.memory import ReplayMemory  # AI의 경험 저장소

app = FastAPI()

# 1. 데이터 규격 정의 (하윤이가 언리얼에서 보내줄 데이터 양식)
class EnvState(BaseModel):
    position: list      # [x, y, z]
    velocity: list      # [vx, vy, vz]
    target_dist: float = 0.0  # 목표물까지의 거리

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "message": "서버가 정상 작동 중입니다! 🚀"
    }

# 2. 언리얼로부터 데이터를 받아 AI가 판단(Action)을 내리는 곳
@app.post("/act")
async def get_action(state: EnvState):
    # [로그 확인] 하윤이가 보낸 데이터가 서버 터미널에 찍힘
    print(f"📍 수신된 위치: {state.position} | 🎯 목표 거리: {state.target_dist}")

    # TODO: 나중에 여기서 RL_Trainer의 모델을 호출하여 실제 AI 판단을 내립니다.
    # 예: action = model.predict(state)
    
    # [테스트용 임시 로직] 지금은 일단 '전진' 신호만 보냅니다.
    test_action = [1.0, 0.0] 
    
    return {"action": test_action}

if __name__ == "__main__":
    import uvicorn
    # 이 주소를 알려주면 됨
    uvicorn.run(app, host="0.0.0.0", port=8000)