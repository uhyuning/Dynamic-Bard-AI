// BardAIManager.cpp

#include "BardAIManager.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

UBardAIManager::UBardAIManager()
{
    PrimaryComponentTick.bCanEverTick = false;
}

// ── 채팅 메시지 전송 ──────────────────────────────────────────────────────────
void UBardAIManager::SendChatMessage(const FString& UserMessage)
{
    if (bRequestPending)
    {
        UE_LOG(LogTemp, Warning, TEXT("[BardAI] 이전 요청 처리 중입니다. 잠시 후 다시 시도하세요."));
        return;
    }

    if (UserMessage.IsEmpty())
    {
        UE_LOG(LogTemp, Warning, TEXT("[BardAI] 메시지가 비어있습니다."));
        return;
    }

    // JSON 요청 본문 구성: {"message": "..."}
    TSharedPtr<FJsonObject> JsonBody = MakeShareable(new FJsonObject());
    JsonBody->SetStringField(TEXT("message"), UserMessage);

    FString RequestBody;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&RequestBody);
    FJsonSerializer::Serialize(JsonBody.ToSharedRef(), Writer);

    // HTTP POST 요청 생성
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(ServerUrl + TEXT("/chat"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetContentAsString(RequestBody);
    Request->SetTimeout(TimeoutSeconds);
    Request->OnProcessRequestComplete().BindUObject(this, &UBardAIManager::OnChatResponseReceived);

    bRequestPending = true;
    Request->ProcessRequest();

    UE_LOG(LogTemp, Log, TEXT("[BardAI] 메시지 전송: %s"), *UserMessage);
}

// ── 서버 연결 확인 ────────────────────────────────────────────────────────────
void UBardAIManager::PingServer()
{
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(ServerUrl + TEXT("/"));
    Request->SetVerb(TEXT("GET"));
    Request->SetTimeout(5.0f);
    Request->OnProcessRequestComplete().BindUObject(this, &UBardAIManager::OnPingResponseReceived);
    Request->ProcessRequest();
}

// ── 채팅 응답 처리 ────────────────────────────────────────────────────────────
void UBardAIManager::OnChatResponseReceived(FHttpRequestPtr Request,
                                             FHttpResponsePtr Response,
                                             bool bSuccess)
{
    bRequestPending = false;

    if (!bSuccess || !Response.IsValid())
    {
        FString Error = TEXT("서버에 연결할 수 없습니다. AI 서버(server.py)가 실행 중인지 확인하세요.");
        UE_LOG(LogTemp, Error, TEXT("[BardAI] %s"), *Error);
        OnRequestFailed.Broadcast(Error);
        return;
    }

    if (Response->GetResponseCode() != 200)
    {
        FString Error = FString::Printf(TEXT("서버 오류 (HTTP %d)"), Response->GetResponseCode());
        UE_LOG(LogTemp, Error, TEXT("[BardAI] %s"), *Error);
        OnRequestFailed.Broadcast(Error);
        return;
    }

    // JSON 파싱
    TSharedPtr<FJsonObject> JsonResponse;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());

    if (!FJsonSerializer::Deserialize(Reader, JsonResponse) || !JsonResponse.IsValid())
    {
        FString Error = TEXT("서버 응답을 파싱할 수 없습니다.");
        UE_LOG(LogTemp, Error, TEXT("[BardAI] %s"), *Error);
        OnRequestFailed.Broadcast(Error);
        return;
    }

    // 응답 구조체 채우기
    FChatResponse ChatResponse;
    ChatResponse.Reply             = JsonResponse->GetStringField(TEXT("reply"));
    ChatResponse.Sentiment         = (float)JsonResponse->GetNumberField(TEXT("sentiment"));
    ChatResponse.Arousal           = (float)JsonResponse->GetNumberField(TEXT("arousal"));
    ChatResponse.RecommendedGenre  = JsonResponse->GetStringField(TEXT("recommended_genre"));
    ChatResponse.ActionTaken       = JsonResponse->GetStringField(TEXT("action_taken"));
    ChatResponse.ActionIndex       = (int32)JsonResponse->GetNumberField(TEXT("action_idx"));

    // 상태 업데이트
    LastSentiment = ChatResponse.Sentiment;
    LastGenre     = ChatResponse.RecommendedGenre;

    UE_LOG(LogTemp, Log, TEXT("[BardAI] 응답 수신 | 감정: %.2f | 장르: %s | 행동: %s"),
           ChatResponse.Sentiment, *ChatResponse.RecommendedGenre, *ChatResponse.ActionTaken);

    // ── Blueprint 이벤트 발생 (여기에 UE5 에디터에서 기능을 연결하세요) ────────

    // 1. 대화 응답 → UI 말풍선 등
    OnChatReply.Broadcast(ChatResponse);

    // 2. 음악 장르 변경 → 사운드 에셋 교체
    OnMusicChange.Broadcast(ChatResponse.RecommendedGenre);

    // 3. 분위기 변경 → 조명/포그/날씨 등
    OnAtmosphereChange.Broadcast(ChatResponse.Sentiment, ChatResponse.Arousal);
}

// ── 피드백 전송 ───────────────────────────────────────────────────────────────
void UBardAIManager::SendFeedback(const FString& TrackId, int32 ActionIdx,
                                   const FString& FeedbackType, float ListenDurationPct)
{
    // JSON 요청 본문 구성
    TSharedPtr<FJsonObject> JsonBody = MakeShareable(new FJsonObject());
    JsonBody->SetStringField(TEXT("track_id"), TrackId);
    JsonBody->SetNumberField(TEXT("action_idx"), ActionIdx);
    JsonBody->SetStringField(TEXT("feedback_type"), FeedbackType);
    JsonBody->SetNumberField(TEXT("listen_duration_pct"), ListenDurationPct);

    FString RequestBody;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&RequestBody);
    FJsonSerializer::Serialize(JsonBody.ToSharedRef(), Writer);

    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(ServerUrl + TEXT("/feedback"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetContentAsString(RequestBody);
    Request->SetTimeout(TimeoutSeconds);

    // 피드백은 응답을 별도로 처리하지 않아도 됩니다 (fire and forget)
    Request->OnProcessRequestComplete().BindLambda(
        [FeedbackType, TrackId](FHttpRequestPtr Req, FHttpResponsePtr Resp, bool bSuccess)
        {
            if (bSuccess && Resp.IsValid())
            {
                UE_LOG(LogTemp, Log, TEXT("[BardAI] 피드백 전송 완료: %s (%s)"),
                       *FeedbackType, *TrackId);
            }
        });

    Request->ProcessRequest();
    UE_LOG(LogTemp, Log, TEXT("[BardAI] 피드백 전송 중: %s (청취율 %.0f%%)"),
           *FeedbackType, ListenDurationPct * 100.0f);
}

// ── 핑 응답 처리 ──────────────────────────────────────────────────────────────
void UBardAIManager::OnPingResponseReceived(FHttpRequestPtr Request,
                                             FHttpResponsePtr Response,
                                             bool bSuccess)
{
    if (bSuccess && Response.IsValid() && Response->GetResponseCode() == 200)
    {
        UE_LOG(LogTemp, Log, TEXT("[BardAI] 서버 연결 성공! (%s)"), *ServerUrl);
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("[BardAI] 서버 연결 실패. server.py를 먼저 실행하세요."));
    }
}
