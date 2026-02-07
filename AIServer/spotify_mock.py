import random
import time

class SpotifyMock:
    """
    [입문자 가이드] Spotify API가 점검 중일 때 사용하는 가상 데이터 생성기입니다.
    실제 음악 대신 무작위로 리듬(BPM)과 감정(Energy) 데이터를 만들어줍니다.
    """
    def __init__(self):
        self.genres = ["K-Pop", "Lo-fi", "Hip-hop", "Classical"]
        
    def get_current_track_info(self):
        # 1. 60~160 사이의 무작위 BPM (심장박동 같은 리듬) 생성
        bpm = random.uniform(60, 160)
        
        # 2. 0~1 사이의 음악 에너지 (신나는 정도) 생성
        energy = random.random()
        
        # 3. 0~1 사이의 가변성 (춤추기 좋은 정도) 생성
        danceability = random.random()

        return {
            "name": f"Virtual Track {random.randint(1, 100)}",
            "artist": "AI Composer",
            "bpm": round(bpm, 2),
            "energy": round(energy, 2),
            "danceability": round(danceability, 2),
            "genre": random.choice(self.genres)
        }

#