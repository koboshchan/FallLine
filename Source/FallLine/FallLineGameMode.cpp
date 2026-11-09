#include "FallLineGameMode.h"
#include "SkiPawn.h"
#include "TestSlope.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "HAL/PlatformMisc.h"
AFallLineGameMode::AFallLineGameMode() {
 DefaultPawnClass=ASkiPawn::StaticClass(); PrimaryActorTick.bCanEverTick=true;
}
void AFallLineGameMode::BeginPlay() {
 Super::BeginPlay();
 bool bFound=false; for(TActorIterator<ATestSlope> I(GetWorld());I;++I) bFound=true;
 if(!bFound) GetWorld()->SpawnActor<ATestSlope>();
 if(auto* P=Cast<ASkiPawn>(UGameplayStatics::GetPlayerPawn(this,0))) {
  P->ResetRun(); Start=P->GetActorLocation();
 }
 bSmoke=FParse::Param(FCommandLine::Get(),TEXT("FallLineSmoke"));
 UE_LOG(LogTemp,Display,TEXT("FALLLINE_LEVEL_READY TestSlope smoke=%d"),bSmoke);
}
void AFallLineGameMode::Tick(float Dt) {
 Super::Tick(Dt); if(!bSmoke||bFinished) return;
 const int32 PreviousSecond=FMath::FloorToInt(Elapsed);
 Elapsed+=Dt;
 if(FMath::FloorToInt(Elapsed)!=PreviousSecond) UE_LOG(LogTemp,Display,TEXT("FALLLINE_SMOKE_TICK elapsed=%.2f"),Elapsed);
 auto* P=Cast<ASkiPawn>(UGameplayStatics::GetPlayerPawn(this,0));
 if(P) {
  // BeginPlay pawn order can vary. Establish spawn after first player exists.
  if(Start.IsZero()) {P->ResetRun(); Start=P->GetActorLocation();}
  bSawGround|=P->IsGrounded();
  MaxSpeed=FMath::Max(MaxSpeed,static_cast<float>(P->GetVelocity().Size()));
  P->SetTestInput(Elapsed>3 && Elapsed<5 ? .35f : 0.f,Elapsed>9 ? .4f : 0.f);
  if(Elapsed>6 && !bJumpAttempted && P->IsGrounded()) {P->Jump(); bJumpAttempted=true;}
 }
 if(Elapsed>=12) {
  bFinished=true;
  const bool Pass=P && bSawGround && MaxSpeed>100 && P->GetJumpCount()>0 &&
   !P->GetActorLocation().ContainsNaN() && P->GetActorLocation().X>Start.X+100;
  UE_LOG(LogTemp,Display,TEXT("FALLLINE_SMOKE_%s grounded=%d maxSpeed=%.2f jumps=%d start=%s end=%s"),
   Pass?TEXT("PASS"):TEXT("FAIL"),bSawGround,MaxSpeed,P?P->GetJumpCount():0,*Start.ToString(),P?*P->GetActorLocation().ToString():TEXT("missing"));
  FPlatformMisc::RequestExitWithStatus(false,Pass?0:2);
 }
}
