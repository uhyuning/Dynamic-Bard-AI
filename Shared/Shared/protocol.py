# Shared/protocol.py

class AIProtocol:
    # 1. 에이전트가 관찰하는 것 (State)
    # 예: [나의 X좌표, 나의 Y좌표, 목표물까지의 거리]
    OBSERVATION_SIZE = 3 
    
    # 2. 에이전트가 할 수 있는 행동 (Action)
    # 예: 0: 정지, 1: 전진, 2: 좌회전, 3: 우회전
    ACTION_SIZE = 4