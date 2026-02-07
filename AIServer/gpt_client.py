import os
from dotenv import load_dotenv
from openai import OpenAI

current_file_path = os.path.abspath(__file__) # 현재 파일의 실제 위치
current_dir = os.path.dirname(current_file_path) # AIServer 폴더
project_root = os.path.dirname(current_dir) # UE5_AI_RL_Project 폴더
env_path = os.path.join(project_root, '.env') # 금고의 최종 주소

# .env 파일을 찾아서 비밀번호들을 읽어옵니다.
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ 설정 파일 로드 성공: {env_path}")
else:
    print(f"❌ 설정 파일(.env)을 찾을 수 없습니다: {env_path}")

class GPTController:
    def __init__(self):
        # 이제 시스템 설정에서 API 키를 가져옵니다.
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요!")
            
        self.client = OpenAI(api_key=api_key)

    def get_ai_comment(self, genre, bpm, action):
        try:
            prompt = f"현재 {genre} 음악이 {bpm} BPM으로 나오고 있어. AI는 '{action}'을 하기로 했어. 하윤이에게 짧고 다정한 한마디 해줘."
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 다정한 AI 친구야."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"음악이 너무 좋아서 잠시 감상 중이야! (오류: {e})"