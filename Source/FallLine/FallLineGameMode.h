#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "FallLineGameMode.generated.h"
UCLASS()
class FALLLINE_API AFallLineGameMode : public AGameModeBase {
 GENERATED_BODY()
public:
 AFallLineGameMode();
 virtual void BeginPlay() override;
 virtual void Tick(float Dt) override;
private:
 bool bSmoke=false,bJumpAttempted=false,bSawGround=false,bFinished=false;
 float Elapsed=0,MaxSpeed=0;
 FVector Start=FVector::ZeroVector;
};
