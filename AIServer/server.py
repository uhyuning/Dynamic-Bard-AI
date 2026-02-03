# AIServer/server.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 1. 데이터 규격 정의 (State)
class EnvState(BaseModel):
    position: list
    velocity: list

@app.get("/")
def read_root():
    return {"message": "AI Server is Running!"}

# 2. 언리얼로부터 데이터를 받는 포트
@app.post("/act")
def get_action(state: EnvState):
    print(f"수신된 환경 데이터: {state.position}")
    # 일단은 테스트용으로 '오른쪽 이동' 신호만 보냄
    return {"action": [1.0, 0.0]}