import os

# 생성할 폴더와 파일 리스트 정의
structure = [
    "UnrealProject/Plugins",
    "AIServer",
    "RL_Trainer/envs",
    "RL_Trainer/models",
    "RL_Trainer/checkpoints",
    "Shared"
]

files = {
    "AIServer/server.py": "# FastAPI Server for UE5 Communication",
    "AIServer/inference.py": "# Model Inference Script",
    "RL_Trainer/train.py": "# RL Training Script",
    "requirements.txt": "torch\ngymnasium\nstable-baselines3\nfastapi\nuvicorn"
}

# 폴더 생성
for folder in structure:
    os.makedirs(folder, exist_ok=True)
    print(f"폴더 생성 완료: {folder}")

# 기본 파일 생성
for file_path, content in files.items():
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"파일 생성 완료: {file_path}")

print("\n--- 프로젝트 세팅이 완료되었습니다! ---")