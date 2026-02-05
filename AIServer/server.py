# AIServer/server.py
from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os

# Shared 폴더를 참조하기 위한 경로 설정 (입문자라면 이 부분이 생소할 수 있어요!)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
# from Shared.protocol import AIProtocol  # 나중에 protocol.py를 만들면 사용하세요!

app = FastAPI()

# 1. 데이터 규격 정의 (구조화된 데이터)
class EnvState(BaseModel):
    position: list  # [x, y, z]
    velocity: list  # [vx, vy, vz]
    target_dist: float = 0.0 # 목표물까지의 거리 (추가 예시)

@app.get("/")
def read_root():
    return {"status": "online", "message": "AI Server for Unreal Engine is Running!"}

# 2. 언리얼로부터 데이터를 받아 행동(Action)을 결정하는 곳
@app.post("/act")
def get_action(state: EnvState):
    # 여기서 나중에 질문자님이 강화학습 모델(AI)을 돌리게 됩니다.
    print(f"수신된 환경 데이터 - 위치: {state.position}")
    
    # [테스트 로직] 목표물 거리가 멀면 앞으로(1.0), 가까우면 멈춤(0.0) 등
    action = [1.0, 0.0] 
    
    return {"action": action}