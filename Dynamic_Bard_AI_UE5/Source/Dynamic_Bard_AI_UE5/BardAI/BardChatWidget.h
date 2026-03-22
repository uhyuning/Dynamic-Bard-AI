// BardChatWidget.h
// Dynamic Bard AI — 채팅 UI 위젯 베이스 클래스
//
// [역할]
//   사용자가 텍스트를 입력하고 AI 응답을 보는 채팅 UI의 C++ 기반 클래스입니다.
//
// [여자친구에게]
//   UE5 에디터에서 이 클래스를 부모로 하는 Widget Blueprint를 만드세요:
//     콘텐츠 브라우저 우클릭 → User Interface → Widget Blueprint
//     → 부모 클래스 검색: BardChatWidget 선택
//
//   그 다음 Widget Blueprint 안에서:
//     - ChatInputBox   : 텍스트 입력 박스를 이 이름으로 바인딩
//     - ChatOutputBox  : 대화 내용 표시 박스를 이 이름으로 바인딩
//     - SendButton     : 전송 버튼을 이 이름으로 바인딩
//     - SentimentBar   : 감정 표시 Progress Bar (선택사항)
//   (이름만 맞추면 자동으로 연결됩니다)

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "BardAIManager.h"
#include "BardChatWidget.generated.h"

class UEditableTextBox;
class UTextBlock;
class UButton;
class UProgressBar;
class UScrollBox;

UCLASS()
class DYNAMIC_BARD_AI_UE5_API UBardChatWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeConstruct() override;

    // BardAIManager 컴포넌트를 연결합니다 (BeginPlay에서 호출)
    UFUNCTION(BlueprintCallable, Category = "Bard Chat")
    void SetAIManager(UBardAIManager* Manager);

    // 메시지 전송 (버튼 클릭 또는 엔터키)
    UFUNCTION(BlueprintCallable, Category = "Bard Chat")
    void SubmitMessage();

protected:
    // ── Widget Blueprint에서 이름으로 바인딩할 UI 요소들 ──────────────────────
    // 이름을 정확히 맞춰야 자동 연결됩니다.

    // 사용자 입력 텍스트 박스 (이름: "ChatInputBox")
    UPROPERTY(meta = (BindWidgetOptional))
    TObjectPtr<UEditableTextBox> ChatInputBox;

    // 대화 내용 출력 텍스트 (이름: "ChatOutputBox")
    UPROPERTY(meta = (BindWidgetOptional))
    TObjectPtr<UTextBlock> ChatOutputBox;

    // 전송 버튼 (이름: "SendButton")
    UPROPERTY(meta = (BindWidgetOptional))
    TObjectPtr<UButton> SendButton;

    // 감정 게이지 Progress Bar, 0=부정 / 1=긍정 (이름: "SentimentBar", 선택사항)
    UPROPERTY(meta = (BindWidgetOptional))
    TObjectPtr<UProgressBar> SentimentBar;

    // 대화 스크롤 박스 (이름: "ChatScrollBox", 선택사항)
    UPROPERTY(meta = (BindWidgetOptional))
    TObjectPtr<UScrollBox> ChatScrollBox;

    // ── Blueprint에서 override 가능한 이벤트 ─────────────────────────────────

    // AI 응답 수신 시 호출됩니다 (애니메이션, 이펙트 등 추가 가능)
    UFUNCTION(BlueprintNativeEvent, Category = "Bard Chat")
    void OnResponseReceived(const FChatResponse& Response);
    virtual void OnResponseReceived_Implementation(const FChatResponse& Response);

    // 음악 변경 시 호출됩니다
    UFUNCTION(BlueprintNativeEvent, Category = "Bard Chat")
    void OnMusicChanged(const FString& Genre);
    virtual void OnMusicChanged_Implementation(const FString& Genre);

private:
    UFUNCTION()
    void HandleChatReply(const FChatResponse& Response);

    UFUNCTION()
    void HandleMusicChange(const FString& Genre);

    UFUNCTION()
    void HandleRequestFailed(const FString& ErrorMessage);

    UFUNCTION()
    void OnSendButtonClicked();

    UPROPERTY()
    TObjectPtr<UBardAIManager> AIManager;

    FString ConversationLog;  // 전체 대화 누적 텍스트
};
