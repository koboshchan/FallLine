#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "InputActionValue.h"
#include "SkiPawn.generated.h"
class UBoxComponent;
class UStaticMeshComponent;
class UPoseableMeshComponent;
class USpringArmComponent;
class UCameraComponent;
class UInputMappingContext;
class UInputAction;
class UPhysicalMaterial;

UCLASS()
class FALLLINE_API ASkiPawn : public APawn {
 GENERATED_BODY()
public:
 ASkiPawn();
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
 virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
 void Jump();
 void ResetRun();
 bool IsGrounded() const {return bGrounded;}
 bool IsGrinding() const {return bGrinding;}
 int32 GetJumpCount() const {return JumpCount;}
 int32 GetGrindFrames() const {return GrindFrames;}
 void SetTestInput(float Turn, float Brake) { Steering=Turn; Braking=Brake; }
 UPROPERTY(EditAnywhere, Category="Ski physics") float EdgeGrip=7.f;
 UPROPERTY(EditAnywhere, Category="Ski physics") float FlatGrip=0.7f;
 UPROPERTY(EditAnywhere, Category="Ski physics") float SidecutRadius=1400.f;
 UPROPERTY(EditAnywhere, Category="Ski physics") float JumpSpeed=450.f;
 UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> Body;
private:
 UPROPERTY() TObjectPtr<USceneComponent> VisualRoot;
 UPROPERTY() TObjectPtr<UPoseableMeshComponent> SkierMesh;
 UPROPERTY() TObjectPtr<UStaticMeshComponent> LeftSki;
 UPROPERTY() TObjectPtr<UStaticMeshComponent> RightSki;
 void UpdateSkierPose(float Dt, const FVector& Velocity);
 float VisualCrouch=0, VisualSteer=0, LandingCompression=0, PreviousVerticalSpeed=0;
 bool bVisualWasGrounded=false;
 UPROPERTY() TObjectPtr<USpringArmComponent> CameraBoom;
 UPROPERTY() TObjectPtr<UCameraComponent> Camera;
 UPROPERTY() TObjectPtr<UPhysicalMaterial> SkiMaterial;
 UPROPERTY() TObjectPtr<UInputMappingContext> SkiMapping;
 UPROPERTY() TObjectPtr<UInputAction> SteerAction;
 UPROPERTY() TObjectPtr<UInputAction> BrakeAction;
 UPROPERTY() TObjectPtr<UInputAction> PushAction;
 UPROPERTY() TObjectPtr<UInputAction> JumpAction;
 UPROPERTY() TObjectPtr<UInputAction> ResetAction;
 UPROPERTY() TObjectPtr<UInputAction> LookAction;
 void Steer(const FInputActionValue& V);
 void Brake(const FInputActionValue& V);
 void Push(const FInputActionValue& V);
 void Look(const FInputActionValue& V);
 float Steering=0, Braking=0, Pushing=0, JumpCooldown=0;
 bool bGrounded=false, bGrinding=false;
 int32 JumpCount=0, GrindFrames=0;
 FVector GroundNormal=FVector::UpVector;
};
