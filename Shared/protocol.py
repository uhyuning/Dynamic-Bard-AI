# Shared/protocol.py
from pydantic import BaseModel

class EnvState(BaseModel):
    position: list      # [x, y, z]
    velocity: list      # [vx, vy, vz]
    target_dist: float = 0.0

class AIResponse(BaseModel):
    action: list
    message: str = ""