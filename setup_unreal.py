import os
import json

# 1. 언리얼 프로젝트 경로 설정
unreal_root = "UnrealProject"

# 2. 생성할 하위 폴더 리스트
folders = [
    f"{unreal_root}/Content/Maps",       # 맵 저장
    f"{unreal_root}/Content/Blueprints", # AI 로직 저장
    f"{unreal_root}/Content/Assets",     # 하윤이의 악기/디자인 파일
    f"{unreal_root}/Config",             # 설정 파일
    f"{unreal_root}/Plugins",            # 아까 만든 플러그인 폴더
    f"{unreal_root}/Source"              # C++ 코드 (필요 시)
]

# 3. .uproject 파일에 들어갈 기본 내용
uproject_data = {
    "FileVersion": 3,
    "EngineAssociation": "5.4", # 본인의 언리얼 버전에 맞게 수정 (예: 5.3, 5.4)
    "Category": "",
    "Description": "UE5 AI RL Project with Hayun",
    "Plugins": [
        {
            "Name": "ModelingToolsEditorMode",
            "Enabled": True,
            "TargetAllowList": ["Editor"]
        }
    ]
}

# 폴더 생성
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"폴더 생성 완료: {folder}")

# .uproject 파일 생성 (이름은 프로젝트명에 맞춰 생성)
uproject_path = os.path.join(unreal_root, "MyAIRLProject.uproject")
with open(uproject_path, "w", encoding="utf-8") as f:
    json.dump(uproject_data, f, indent=4)
    print(f"파일 생성 완료: {uproject_path}")

print("\n--- 언리얼 프로젝트 뼈대 생성 완료! ---")