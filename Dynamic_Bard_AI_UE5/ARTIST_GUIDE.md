# Dynamic Bard AI — 에셋 교체 가이드 (UE5 작업자용)

> 안녕! 이 문서는 UE5 에디터에서 그래픽/사운드를 붙이는 방법을 설명해.
> C++ 코드는 이미 다 작성되어 있으니까, 아래 순서대로만 하면 돼.

---

## 먼저 해야 할 것: AI 서버 실행

UE5에서 플레이하기 전에, 백엔드 서버를 먼저 켜야 해.
터미널에서 프로젝트 루트(`UE5_AI_RL_Project/`)로 이동한 후:

```
python AIServer/server.py
```

`http://localhost:8000` 에서 서버가 실행되면 준비 완료.

---

## Step 1: 캐릭터 교체

현재 프로젝트에는 언리얼 기본 마네킹(Mannequin)이 들어있어.
원하는 캐릭터로 교체하는 방법:

1. **캐릭터 임포트**: `Content Browser` → `Import` → `.fbx` 파일 선택
2. **Skeleton 설정**: 임포트할 때 "Use Existing Skeleton"이나 "Create New Skeleton" 선택
3. **캐릭터 교체**:
   - `Content/Characters/Mannequins/` 폴더에 있는 기존 메쉬를 대체하거나
   - 새 Blueprint를 만들어서 "Parent Class: Character"로 설정 후 메쉬 교체

**TIP**: 임포트된 `.fbx`는 자동으로 `.uasset`으로 변환돼서 프로젝트에 영구 저장돼.

---

## Step 2: BardAIManager 컴포넌트 붙이기

AI 채팅 기능을 캐릭터에 붙이는 방법:

1. 원하는 캐릭터 Blueprint 열기 (더블클릭)
2. 좌측 `Components` 패널 → `Add` 클릭
3. `BardAIManager` 검색 → 추가
4. `Details` 패널에서 `Server Url` 확인 (`http://localhost:8000` 이 기본값)

---

## Step 3: 채팅 UI 만들기

1. `Content Browser` 우클릭 → `User Interface` → `Widget Blueprint`
2. 부모 클래스를 `BardChatWidget`으로 설정
3. 위젯 에디터에서 아래 UI 요소들을 만들고 **이름을 정확히** 맞춰:

| UI 요소 종류 | 반드시 사용할 이름 | 역할 |
|------------|-----------------|------|
| Editable Text Box | `ChatInputBox` | 사용자 입력창 |
| Text Block | `ChatOutputBox` | 대화 내용 표시 |
| Button | `SendButton` | 전송 버튼 |
| Progress Bar | `SentimentBar` | 감정 게이지 (선택사항) |

4. 위젯을 화면에 띄우는 Blueprint 작성 (BeginPlay에 Add to Viewport 연결)
5. `SetAIManager` 함수 호출해서 BardAIManager와 연결

---

## Step 4: 음악 연결

`BardAIManager`의 **OnMusicChange** 이벤트에 원하는 사운드를 연결해:

```
[OnMusicChange (Genre 문자열)]
  → Switch on String (Genre)
      "Lo-fi"      → Play Sound: [로파이 사운드 에셋]
      "K-Pop"      → Play Sound: [케이팝 사운드 에셋]
      "Hip-hop"    → Play Sound: [힙합 사운드 에셋]
      "Classical"  → Play Sound: [클래식 사운드 에셋]
```

**사운드 임포트**: `Content Browser` → `Import` → `.mp3` 또는 `.wav` 파일

---

## Step 5: 분위기 변경 연결 (선택사항)

`BardAIManager`의 **OnAtmosphereChange** 이벤트:
- `Sentiment` 값: -1(부정) ~ 1(긍정)
- `Arousal` 값: 0(차분) ~ 1(활발)

이 값으로 조명, 포그, 날씨, 맵 색상 등을 조절하면 돼:

```
[OnAtmosphereChange (Sentiment, Arousal)]
  → Sky Light Intensity = (Sentiment + 1) / 2 * 3.0
  → Fog Density = (1 - Sentiment) * 0.05
  → Post Process Saturation = Arousal
```

---

## 이벤트 요약표

| 이벤트 이름 | 언제 발생? | 전달되는 값 | 추천 연결 대상 |
|-----------|----------|-----------|------------|
| `OnChatReply` | AI 응답 도착 시 | FChatResponse (전체 응답) | 말풍선, 캐릭터 애니 |
| `OnMusicChange` | 음악 장르 변경 시 | Genre (문자열) | 사운드 에셋 교체 |
| `OnAtmosphereChange` | 감정 변화 시 | Sentiment, Arousal | 조명/포그/날씨 |
| `OnRequestFailed` | 서버 오류 시 | ErrorMessage | 에러 UI 표시 |

---

## 자주 묻는 것들

**Q: 플레이해도 AI가 반응하지 않아요**
A: 터미널에서 `python AIServer/server.py`가 실행 중인지 확인. `http://localhost:8000`을 브라우저에서 열어서 `"status": "online"`이 나오면 OK.

**Q: 사운드를 넣었는데 장르가 바뀌어도 음악이 안 바뀌어요**
A: `OnMusicChange` 이벤트가 `BardAIManager` 컴포넌트에 연결되어 있는지 확인.

**Q: 캐릭터 애니메이션을 감정에 따라 바꾸고 싶어요**
A: `OnChatReply` 이벤트에서 `Response.Sentiment` 값을 읽어서 Animation Blueprint로 전달하면 돼.

**Q: 채팅창 디자인을 바꾸고 싶어요**
A: Widget Blueprint 안에서 자유롭게 꾸며도 돼. 위 이름 규칙만 지키면 기능은 유지돼.
