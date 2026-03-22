// BardChatWidget.cpp

#include "BardChatWidget.h"
#include "Components/EditableTextBox.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/ProgressBar.h"
#include "Components/ScrollBox.h"

void UBardChatWidget::NativeConstruct()
{
    Super::NativeConstruct();

    // 전송 버튼 클릭 이벤트 연결
    if (SendButton)
    {
        SendButton->OnClicked.AddDynamic(this, &UBardChatWidget::OnSendButtonClicked);
    }

    // 초기 감정 게이지: 중립(0.5)
    if (SentimentBar)
    {
        SentimentBar->SetPercent(0.5f);
    }
}

void UBardChatWidget::SetAIManager(UBardAIManager* Manager)
{
    if (!Manager) return;

    AIManager = Manager;

    // BardAIManager의 이벤트를 이 위젯의 핸들러에 연결
    Manager->OnChatReply.AddDynamic(this, &UBardChatWidget::HandleChatReply);
    Manager->OnMusicChange.AddDynamic(this, &UBardChatWidget::HandleMusicChange);
    Manager->OnRequestFailed.AddDynamic(this, &UBardChatWidget::HandleRequestFailed);
}

void UBardChatWidget::SubmitMessage()
{
    if (!AIManager)
    {
        UE_LOG(LogTemp, Warning, TEXT("[BardChat] AIManager가 연결되지 않았습니다. SetAIManager()를 호출하세요."));
        return;
    }

    if (!ChatInputBox) return;

    FString UserMessage = ChatInputBox->GetText().ToString().TrimStartAndEnd();
    if (UserMessage.IsEmpty()) return;

    // 내 메시지를 대화창에 표시
    ConversationLog += FString::Printf(TEXT("나: %s\n"), *UserMessage);
    if (ChatOutputBox)
    {
        ChatOutputBox->SetText(FText::FromString(ConversationLog));
    }

    // 입력창 초기화
    ChatInputBox->SetText(FText::GetEmpty());

    // AI 서버로 전송
    AIManager->SendChatMessage(UserMessage);
}

// ── 내부 이벤트 핸들러 ────────────────────────────────────────────────────────
void UBardChatWidget::OnSendButtonClicked()
{
    SubmitMessage();
}

void UBardChatWidget::HandleChatReply(const FChatResponse& Response)
{
    // AI 응답을 대화창에 추가
    ConversationLog += FString::Printf(TEXT("AI: %s\n\n"), *Response.Reply);
    if (ChatOutputBox)
    {
        ChatOutputBox->SetText(FText::FromString(ConversationLog));
    }

    // 감정 게이지 업데이트: sentiment (-1~1) → (0~1)로 변환
    if (SentimentBar)
    {
        float BarValue = (Response.Sentiment + 1.0f) / 2.0f;
        SentimentBar->SetPercent(BarValue);
    }

    // Blueprint에서 override 가능한 이벤트 호출 (애니메이션 등 추가 가능)
    OnResponseReceived(Response);
}

void UBardChatWidget::HandleMusicChange(const FString& Genre)
{
    UE_LOG(LogTemp, Log, TEXT("[BardChat] 음악 변경 → %s"), *Genre);
    OnMusicChanged(Genre);
}

void UBardChatWidget::HandleRequestFailed(const FString& ErrorMessage)
{
    ConversationLog += FString::Printf(TEXT("[오류] %s\n"), *ErrorMessage);
    if (ChatOutputBox)
    {
        ChatOutputBox->SetText(FText::FromString(ConversationLog));
    }
}

// ── Blueprint에서 override 가능한 기본 구현 ───────────────────────────────────
void UBardChatWidget::OnResponseReceived_Implementation(const FChatResponse& Response)
{
    // 기본 구현: 로그만 출력
    // Blueprint에서 이 함수를 override해서 캐릭터 애니메이션 등을 추가하세요
    UE_LOG(LogTemp, Log, TEXT("[BardChat] 응답 수신 | 감정: %.2f | 장르: %s"),
           Response.Sentiment, *Response.RecommendedGenre);
}

void UBardChatWidget::OnMusicChanged_Implementation(const FString& Genre)
{
    // 기본 구현: 로그만 출력
    // Blueprint에서 이 함수를 override해서 사운드 에셋을 교체하세요
    UE_LOG(LogTemp, Log, TEXT("[BardChat] 음악 → %s"), *Genre);
}
