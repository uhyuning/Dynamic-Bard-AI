import os
import json
from dotenv import load_dotenv
from openai import OpenAI

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')

if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ 설정 파일 로드 성공: {env_path}")
else:
    print(f"❌ 설정 파일(.env)을 찾을 수 없습니다: {env_path}")


class GPTController:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요!")
        self.client = OpenAI(api_key=api_key)

    def analyze_and_reply(self, user_message: str,
                          current_genre: str = "",
                          current_bpm: float = 100.0) -> dict:
        """
        사용자 메시지를 받아 대화 응답 + 감정 분석을 동시에 수행합니다.

        Returns:
            {
                "reply": str,       # AI 대화 응답
                "sentiment": float, # 감정 점수 (-1.0 ~ 1.0)
                "arousal": float,   # 에너지 수준 (0.0 ~ 1.0)
            }
        """
        system_prompt = (
            "너는 사용자의 감정을 세심하게 읽는 다정한 AI 친구야. "
            "사용자의 메시지에 자연스럽게 대화로 답하되, "
            "항상 아래 JSON 형식으로만 응답해:\n"
            "{\n"
            '  "reply": "사용자에게 보낼 따뜻한 한국어 응답 (1~2문장)",\n'
            '  "sentiment": 0.0,\n'
            '  "arousal": 0.0\n'
            "}\n"
            "sentiment: -1.0(매우 부정/우울) ~ 1.0(매우 긍정/행복) 사이 숫자.\n"
            "arousal: 0.0(매우 차분) ~ 1.0(매우 흥분/활발) 사이 숫자.\n"
            "반드시 valid JSON만 출력하고 다른 텍스트는 포함하지 마."
        )

        music_context = ""
        if current_genre:
            music_context = f"\n(현재 재생 중인 음악: {current_genre}, {current_bpm:.0f} BPM)"

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message + music_context}
                ],
                max_tokens=200,
                temperature=0.7
            )
            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)

            # 값 범위 강제 클램핑
            sentiment = max(-1.0, min(1.0, float(data.get("sentiment", 0.0))))
            arousal = max(0.0, min(1.0, float(data.get("arousal", 0.5))))
            reply = str(data.get("reply", "그렇구나, 말해줘서 고마워."))

            return {"reply": reply, "sentiment": sentiment, "arousal": arousal}

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # JSON 파싱 실패 시 원문을 reply로 사용하고 중립 감정 반환
            print(f"⚠️ GPT 응답 파싱 실패: {e}")
            return {"reply": "그렇구나, 조금 더 얘기해줄래?", "sentiment": 0.0, "arousal": 0.5}

        except Exception as e:
            print(f"⚠️ GPT API 오류: {e}")
            return {"reply": "지금 잠깐 생각 중이야, 조금만 기다려줘!", "sentiment": 0.0, "arousal": 0.3}
