"""
AIServer/spotify_client.py — 실제 Spotify API 클라이언트

[필요 환경변수 (.env)]
  SPOTIFY_CLIENT_ID     : Spotify Developer 앱 Client ID
  SPOTIFY_CLIENT_SECRET : Spotify Developer 앱 Client Secret
  SPOTIFY_REDIRECT_URI  : 보통 http://localhost:8888/callback

[Spotify Developer 앱 만들기]
  1. https://developer.spotify.com/dashboard 접속
  2. "Create app" 클릭
  3. Redirect URI에 http://localhost:8888/callback 추가
  4. Client ID / Client Secret을 .env에 저장

[연결 실패 시]
  SpotifyMock으로 자동 대체됩니다 (서버는 계속 작동).

[RL 행동 → Spotify 음악 특성 매핑]
  0: 잔잔 → 저에너지, 고어쿠스틱 (ambient/sleep 계열)
  1: 신남 → 고에너지, 고밸런스 (pop/k-pop 계열)
  2: 감성 → 중에너지, 고밸런스 (indie/r&b 계열)
  3: 집중 → 저에너지, 무드 중립, 고인스트루멘탈 (classical/piano 계열)
"""

import os
import random
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
load_dotenv(os.path.join(project_root, '.env'))

# ── RL 행동 → Spotify 추천 파라미터 매핑 ─────────────────────────────────────
ACTION_SPOTIFY_PARAMS = {
    0: {  # 잔잔 (Lo-fi / Ambient)
        "seed_genres": ["ambient", "sleep"],
        "target_energy": 0.25,
        "target_valence": 0.35,
        "target_tempo": 75.0,
        "target_acousticness": 0.8,
        "max_energy": 0.5,
        "label": "잔잔한 음악",
    },
    1: {  # 신남 (K-Pop / Pop)
        "seed_genres": ["k-pop", "pop"],
        "target_energy": 0.85,
        "target_valence": 0.85,
        "target_tempo": 128.0,
        "min_energy": 0.6,
        "label": "신나는 음악",
    },
    2: {  # 감성 (Indie / R&B)
        "seed_genres": ["indie", "r-n-b"],
        "target_energy": 0.5,
        "target_valence": 0.65,
        "target_tempo": 95.0,
        "label": "감성적인 음악",
    },
    3: {  # 집중 (Classical / Piano)
        "seed_genres": ["classical", "piano"],
        "target_energy": 0.3,
        "target_valence": 0.45,
        "target_tempo": 88.0,
        "target_instrumentalness": 0.7,
        "max_energy": 0.55,
        "label": "집중용 음악",
    },
}


class SpotifyController:
    """
    실제 Spotify Web API 클라이언트.
    인증 정보가 없으면 Mock 모드로 자동 전환됩니다.
    """

    def __init__(self):
        self.sp = None
        self._mock_mode = False
        self._try_connect()

    def _try_connect(self):
        client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

        if not client_id or not client_secret:
            print("[Spotify] 인증 정보 없음. Mock 모드로 실행합니다.")
            print("[Spotify] .env에 SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET을 추가하면 실제 연동됩니다.")
            self._mock_mode = True
            return

        try:
            import spotipy
            from spotipy.oauth2 import SpotifyOAuth

            scope = " ".join([
                "user-read-playback-state",
                "user-modify-playback-state",
                "user-read-currently-playing",
                "user-read-recently-played",
                "streaming",
            ])

            cache_path = os.path.join(project_root, ".spotify_cache")
            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                cache_path=cache_path,
                open_browser=True,
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            # 연결 테스트
            self.sp.current_user()
            print(f"[Spotify] 연결 성공!")

        except ImportError:
            print("[Spotify] spotipy 미설치. pip install spotipy 후 재시작하세요.")
            self._mock_mode = True
        except Exception as e:
            print(f"[Spotify] 연결 실패: {e}. Mock 모드로 실행합니다.")
            self._mock_mode = True

    def is_connected(self) -> bool:
        return self.sp is not None and not self._mock_mode

    def get_recommendations_for_action(self, action_idx: int,
                                        sentiment: float,
                                        limit: int = 5) -> list[dict]:
        """
        RL 행동(action_idx)과 현재 감정(sentiment)을 기반으로
        Spotify에서 실제 트랙을 추천받습니다.

        Returns:
            list of track dicts with audio features
        """
        if self._mock_mode or not self.sp:
            return self._mock_recommendations(action_idx, limit)

        params = ACTION_SPOTIFY_PARAMS.get(action_idx, ACTION_SPOTIFY_PARAMS[0])

        # 감정에 따라 valence 타겟을 약간 조정
        # 슬플 때는 valence를 낮추고, 기쁠 때는 높임
        valence_adjust = sentiment * 0.1  # -0.1 ~ +0.1
        target_valence = max(0.1, min(0.9,
            params["target_valence"] + valence_adjust
        ))

        try:
            # Spotify Recommendations API 호출
            rec_kwargs = {
                "seed_genres": params["seed_genres"],
                "target_energy": params["target_energy"],
                "target_valence": target_valence,
                "target_tempo": params["target_tempo"],
                "limit": limit,
            }
            # 옵션 파라미터 추가
            for opt_key in ("target_acousticness", "target_instrumentalness",
                            "min_energy", "max_energy"):
                if opt_key in params:
                    rec_kwargs[opt_key] = params[opt_key]

            results = self.sp.recommendations(**rec_kwargs)
            tracks = results.get("tracks", [])

            if not tracks:
                print(f"[Spotify] 추천 결과 없음. Mock으로 대체.")
                return self._mock_recommendations(action_idx, limit)

            # 각 트랙의 Audio Features 가져오기
            track_ids = [t["id"] for t in tracks if t.get("id")]
            features_list = self.sp.audio_features(track_ids) or []
            features_map = {f["id"]: f for f in features_list if f}

            result = []
            for track in tracks:
                tid = track.get("id", "")
                feat = features_map.get(tid, {})
                artists = ", ".join(a["name"] for a in track.get("artists", []))

                result.append({
                    "track_id": tid,
                    "name": track.get("name", "Unknown"),
                    "artist": artists,
                    "preview_url": track.get("preview_url") or "",
                    "spotify_uri": track.get("uri", ""),
                    "spotify_url": track.get("external_urls", {}).get("spotify", ""),
                    "energy": feat.get("energy", params["target_energy"]),
                    "valence": feat.get("valence", target_valence),
                    "tempo": feat.get("tempo", params["target_tempo"]),
                    "danceability": feat.get("danceability", 0.5),
                    "acousticness": feat.get("acousticness", 0.5),
                    "mood_label": params["label"],
                    # Mock과의 호환을 위해 유지
                    "genre": params["seed_genres"][0],
                    "bpm": feat.get("tempo", params["target_tempo"]),
                })
            return result

        except Exception as e:
            print(f"[Spotify] 추천 API 오류: {e}. Mock으로 대체.")
            return self._mock_recommendations(action_idx, limit)

    def get_audio_features(self, track_id: str) -> dict | None:
        """특정 트랙의 오디오 특성을 가져옵니다."""
        if not self.sp:
            return None
        try:
            features = self.sp.audio_features([track_id])
            return features[0] if features else None
        except Exception as e:
            print(f"[Spotify] Audio Features 조회 실패: {e}")
            return None

    def get_recently_played(self, limit: int = 20) -> list[dict]:
        """최근 재생 목록을 가져옵니다 (RL 히스토리 분석용)."""
        if not self.sp:
            return []
        try:
            results = self.sp.current_user_recently_played(limit=limit)
            items = results.get("items", [])
            tracks = []
            for item in items:
                track = item.get("track", {})
                tracks.append({
                    "track_id": track.get("id", ""),
                    "name": track.get("name", ""),
                    "artist": ", ".join(a["name"] for a in track.get("artists", [])),
                    "played_at": item.get("played_at", ""),
                })
            return tracks
        except Exception as e:
            print(f"[Spotify] 최근 재생 조회 실패: {e}")
            return []

    def get_current_track(self) -> dict | None:
        """현재 재생 중인 트랙 정보를 가져옵니다."""
        if not self.sp:
            return None
        try:
            current = self.sp.current_playback()
            if not current or not current.get("item"):
                return None
            track = current["item"]
            return {
                "track_id": track.get("id", ""),
                "name": track.get("name", ""),
                "artist": ", ".join(a["name"] for a in track.get("artists", [])),
                "is_playing": current.get("is_playing", False),
                "progress_ms": current.get("progress_ms", 0),
                "duration_ms": track.get("duration_ms", 1),
            }
        except Exception as e:
            print(f"[Spotify] 현재 재생 조회 실패: {e}")
            return None

    # ── Mock 모드 ──────────────────────────────────────────────────────────────
    def _mock_recommendations(self, action_idx: int, limit: int) -> list[dict]:
        """Spotify 미연결 시 가상 트랙 데이터를 반환합니다."""
        params = ACTION_SPOTIFY_PARAMS.get(action_idx, ACTION_SPOTIFY_PARAMS[0])

        mock_tracks = {
            0: [("Rainy Day Lofi", "Lofi Girl"), ("Sleepy Study", "ChillHop"), ("Cozy Cafe", "Ambient Works")],
            1: [("Dynamite", "BTS"), ("Fancy", "TWICE"), ("Next Level", "aespa")],
            2: [("Stay", "The Kid LAROI"), ("drivers license", "Olivia Rodrigo"), ("Blinding Lights", "The Weeknd")],
            3: [("Clair de Lune", "Debussy"), ("Nocturne in E-flat", "Chopin"), ("Gymnopédie No.1", "Satie")],
        }
        candidates = mock_tracks.get(action_idx, mock_tracks[0])

        results = []
        for name, artist in candidates[:limit]:
            results.append({
                "track_id": f"mock_{action_idx}_{name.replace(' ', '_')}",
                "name": name,
                "artist": artist,
                "preview_url": "",
                "spotify_uri": "",
                "spotify_url": "",
                "energy": params["target_energy"] + random.uniform(-0.1, 0.1),
                "valence": params["target_valence"] + random.uniform(-0.1, 0.1),
                "tempo": params["target_tempo"] + random.uniform(-10, 10),
                "danceability": random.uniform(0.3, 0.7),
                "acousticness": random.uniform(0.2, 0.8),
                "mood_label": params["label"],
                "genre": params["seed_genres"][0],
                "bpm": params["target_tempo"],
            })
        return results
