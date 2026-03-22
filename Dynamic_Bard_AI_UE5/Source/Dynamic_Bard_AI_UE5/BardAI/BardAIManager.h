// BardAIManager.h
// Dynamic Bard AI — 서버 통신 매니저
//
// [역할]
//   사용자 채팅 메시지를 AI 서버(FastAPI, port 8000)로 전송하고,
//   서버의 응답(감정 분석 + 음악 추천)을 받아 Blueprint 이벤트로 전달합니다.
//
// [여자친구에게]
//   이 파일은 건드리지 않아도 됩니다.
//   UE5 에디터에서 이 컴포넌트를 원하는 Actor(캐릭터 등)에 붙이고,
//   아래 Blueprint 이벤트들을 원하는 기능에 연결하면 됩니다:
//
//   ★ OnChatReply       → AI 응답 텍스트를 말풍선/UI에 표시
//   ★ OnMusicChange     → 추천 장르에 맞는 사운드 에셋 재생
//   ★ OnAtmosphereChange → 맵 분위기 변경 (조명, 포그, 날씨 등)

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Http.h"
#include "BardAIManager.generated.h"

// ── 서버 응답 구조체 ──────────────────────────────────────────────────────────
// server.py의 ChatResponse와 동일한 필드
USTRUCT(BlueprintType)
struct FChatResponse
{
    GENERATED_BODY()

    // AI의 대화 응답 텍스트
    UPROPERTY(BlueprintReadOnly, Category = "Bard AI")
    FString Reply;

    // 감정 점수: -1.0(매우 부정) ~ 1.0(매우 긍정)
    UPROPERTY(BlueprintReadOnly, Category = "Bard AI")
    float Sentiment = 0.0f;

    // 에너지 수준: 0.0(차분) ~ 1.0(활발)
    UPROPERTY(BlueprintReadOnly, Category = "Bard AI")
    float Arousal = 0.5f;

    // RL이 추천한 음악 장르: "Lo-fi" / "K-Pop" / "Hip-hop" / "Classical"
    UPROPERTY(BlueprintReadOnly, Category = "Bard AI")
    FString RecommendedGenre;

    // RL이 선택한 행동 이름 (한국어 설명)
    UPROPERTY(BlueprintReadOnly, Category = "Bard AI")
    FString ActionTaken;

    // RL 행동 인덱스: 0=잔잔 / 1=신남 / 2=감성 / 3=집중
    UPROPERTY(BlueprintReadOnly, Category = "Bard AI")
    int32 ActionIndex = 0;
};

// ── 델리게이트 선언 (Blueprint 이벤트용) ─────────────────────────────────────
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnChatReply,        const FChatResponse&, Response);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMusicChange,      const FString&,       Genre);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnAtmosphereChange, float, Sentiment, float, Arousal);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnRequestFailed,    const FString&,       ErrorMessage);


// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────
UCLASS(ClassGroup=(BardAI), meta=(BlueprintSpawnableComponent))
class DYNAMIC_BARD_AI_UE5_API UBardAIManager : public UActorComponent
{
    GENERATED_BODY()

public:
    UBardAIManager();

    // ── 설정 ───────────────────────────────────────────────────────────────────
    // AI 서버 주소 (기본값: 로컬 FastAPI 서버)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bard AI|Settings")
    FString ServerUrl = TEXT("http://localhost:8000");

    // 요청 타임아웃 (초)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bard AI|Settings")
    float TimeoutSeconds = 10.0f;

    // ── Blueprint에서 호출할 함수 ──────────────────────────────────────────────

    // 사용자 메시지를 AI 서버로 전송합니다. 응답은 아래 이벤트로 비동기 수신됩니다.
    UFUNCTION(BlueprintCallable, Category = "Bard AI")
    void SendChatMessage(const FString& UserMessage);

    // 서버 연결 상태를 확인합니다 (GET /)
    UFUNCTION(BlueprintCallable, Category = "Bard AI")
    void PingServer();

    // ★ 사용자가 노래를 들은 후 피드백을 전송합니다 (RL 학습의 핵심 신호!)
    // UE5에서 아래 상황에 반드시 호출하세요:
    //   노래 스킵    → SendFeedback(TrackId, ActionIdx, "skipped", 청취비율)
    //   노래 완청    → SendFeedback(TrackId, ActionIdx, "listened", 1.0)
    //   좋아요 버튼  → SendFeedback(TrackId, ActionIdx, "liked", 현재청취비율)
    //   다시 듣기    → SendFeedback(TrackId, ActionIdx, "replayed", 1.0)
    UFUNCTION(BlueprintCallable, Category = "Bard AI")
    void SendFeedback(const FString& TrackId, int32 ActionIdx,
                      const FString& FeedbackType, float ListenDurationPct = 1.0f);

    // ── Blueprint 이벤트 (여기에 원하는 기능을 연결하세요) ────────────────────

    // AI 응답이 도착했을 때 → 말풍선, UI 텍스트 등에 연결
    UPROPERTY(BlueprintAssignable, Category = "Bard AI|Events")
    FOnChatReply OnChatReply;

    // 추천 음악 장르가 변경될 때 → 사운드 에셋 교체에 연결
    // Genre 값: "Lo-fi" / "K-Pop" / "Hip-hop" / "Classical"
    UPROPERTY(BlueprintAssignable, Category = "Bard AI|Events")
    FOnMusicChange OnMusicChange;

    // 감정/에너지 변화 시 → 맵 조명/포그/날씨 변경에 연결
    // Sentiment: -1~1 (부정~긍정), Arousal: 0~1 (차분~활발)
    UPROPERTY(BlueprintAssignable, Category = "Bard AI|Events")
    FOnAtmosphereChange OnAtmosphereChange;

    // 서버 요청 실패 시 → 에러 표시에 연결 (선택사항)
    UPROPERTY(BlueprintAssignable, Category = "Bard AI|Events")
    FOnRequestFailed OnRequestFailed;

    // ── 상태 조회 (읽기 전용) ──────────────────────────────────────────────────
    UFUNCTION(BlueprintPure, Category = "Bard AI")
    bool IsRequestPending() const { return bRequestPending; }

    UFUNCTION(BlueprintPure, Category = "Bard AI")
    float GetLastSentiment() const { return LastSentiment; }

    UFUNCTION(BlueprintPure, Category = "Bard AI")
    FString GetLastGenre() const { return LastGenre; }

private:
    void OnChatResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSuccess);
    void OnPingResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSuccess);

    bool bRequestPending = false;
    float LastSentiment  = 0.0f;
    FString LastGenre    = TEXT("Lo-fi");
};
