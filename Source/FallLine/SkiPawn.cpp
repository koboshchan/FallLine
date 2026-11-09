#include "SkiPawn.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Math/RotationMatrix.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"

ASkiPawn::ASkiPawn() {
 PrimaryActorTick.bCanEverTick=true;
 PrimaryActorTick.TickGroup=TG_PrePhysics;
 Body=CreateDefaultSubobject<UBoxComponent>(TEXT("ChaosSkiBody"));
 SetRootComponent(Body);
 Body->InitBoxExtent(FVector(85,28,12));
 Body->SetCollisionProfileName(TEXT("PhysicsActor"));
 Body->SetSimulatePhysics(true);
 Body->SetEnableGravity(true);
 Body->SetLinearDamping(0.015f);
 Body->SetAngularDamping(4.f);
 Body->BodyInstance.bLockXRotation=true;
 Body->BodyInstance.bLockYRotation=true;
 Body->SetConstraintMode(EDOFMode::SixDOF);
 Body->SetUseCCD(true);
 VisualRoot=CreateDefaultSubobject<USceneComponent>(TEXT("SkierVisual"));
 VisualRoot->SetupAttachment(Body);


 auto Ski=[&](const TCHAR* Name,float Side) {
  auto* P=CreateDefaultSubobject<UStaticMeshComponent>(Name);
  P->SetupAttachment(VisualRoot);
  // Original curved/tapered ski asset is loaded in BeginPlay after import.
  P->SetRelativeLocation(FVector(12,Side,-9));
  P->SetRelativeScale3D(FVector::OneVector);
  P->SetCollisionEnabled(ECollisionEnabled::NoCollision);
  P->SetGenerateOverlapEvents(false);
  return P;
 };
 LeftSki=Ski(TEXT("LeftSki"),-18.f);
 RightSki=Ski(TEXT("RightSki"),18.f);
 // Manny is a real skinned, articulated template mesh. The procedural pose below
 // is visual-only; the existing Chaos box remains the sole simulated body.
 SkierMesh=CreateDefaultSubobject<UPoseableMeshComponent>(TEXT("RiggedSkier"));
 SkierMesh->SetupAttachment(VisualRoot);
 static ConstructorHelpers::FObjectFinder<USkeletalMesh> Manny(
  TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"));
 SkierMesh->SetSkinnedAssetAndUpdate(Manny.Object);
 SkierMesh->SetRelativeRotation(FRotator(0,-90,0));
 SkierMesh->SetRelativeLocation(FVector(0,0,-6));
 SkierMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 SkierMesh->SetGenerateOverlapEvents(false);
 SkierMesh->SetCanEverAffectNavigation(false);
 SkierMesh->BoundsScale=1.6f;
 CameraBoom=CreateDefaultSubobject<USpringArmComponent>(TEXT("ChaseBoom"));
 CameraBoom->SetupAttachment(Body); CameraBoom->TargetArmLength=650;
 CameraBoom->SetRelativeLocation(FVector(0,0,140));
 CameraBoom->bUsePawnControlRotation=true;
 CameraBoom->bEnableCameraLag=true; CameraBoom->CameraLagSpeed=6;
 Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("ChaseCamera"));
 Camera->SetupAttachment(CameraBoom,USpringArmComponent::SocketName);
 Camera->FieldOfView=85;
}
void ASkiPawn::BeginPlay() {
 Super::BeginPlay();
 // Visual-only original ski with curved shovel, sidecut, edges and bindings.
 // No collision is generated/imported and the ChaosSkiBody is unchanged.
 if(auto* SkiMesh=LoadObject<UStaticMesh>(nullptr,
   TEXT("/Game/Equipment/Skis/SM_AlpineSki.SM_AlpineSki"))) {
  LeftSki->SetStaticMesh(SkiMesh);
  RightSki->SetStaticMesh(SkiMesh);
 } else {
  UE_LOG(LogTemp,Error,TEXT("FALLLINE_SKIS_MISSING run ImportSkiGeometry.import_skis before capture"));
 }
 SkiMaterial=NewObject<UPhysicalMaterial>(this);
 SkiMaterial->Friction=0; SkiMaterial->Restitution=0;
 SkiMaterial->bOverrideFrictionCombineMode=true;
 SkiMaterial->FrictionCombineMode=EFrictionCombineMode::Min;
 Body->SetPhysMaterialOverride(SkiMaterial);
 Body->SetMassOverrideInKg(NAME_None,80);
 if(Controller) Controller->SetControlRotation(FRotator(-18,0,0));
 UE_LOG(LogTemp,Display,TEXT("FALLLINE_PAWN_READY Chaos=%d"),Body->IsSimulatingPhysics());
}
void ASkiPawn::SetupPlayerInputComponent(UInputComponent* Input) {
 Super::SetupPlayerInputComponent(Input);
 auto* EI=CastChecked<UEnhancedInputComponent>(Input);
 SkiMapping=NewObject<UInputMappingContext>(this);
 auto Action=[&](const TCHAR* Name,EInputActionValueType Type) {
  auto* A=NewObject<UInputAction>(this,Name); A->ValueType=Type;
  A->AccumulationBehavior=EInputActionAccumulationBehavior::Cumulative;
  return A;
 };
 SteerAction=Action(TEXT("EdgeAngle"),EInputActionValueType::Axis1D);
 BrakeAction=Action(TEXT("Snowplow"),EInputActionValueType::Axis1D);
 PushAction=Action(TEXT("PolePush"),EInputActionValueType::Axis1D);
 JumpAction=Action(TEXT("Pop"),EInputActionValueType::Boolean);
 ResetAction=Action(TEXT("ResetRun"),EInputActionValueType::Boolean);
 LookAction=Action(TEXT("CameraYaw"),EInputActionValueType::Axis1D);
 SkiMapping->MapKey(SteerAction,EKeys::D);
 SkiMapping->MapKey(SteerAction,EKeys::A).Modifiers.Add(NewObject<UInputModifierNegate>(SkiMapping));
 SkiMapping->MapKey(SteerAction,EKeys::Gamepad_LeftX).Modifiers.Add(NewObject<UInputModifierDeadZone>(SkiMapping));
 SkiMapping->MapKey(BrakeAction,EKeys::S);
 SkiMapping->MapKey(BrakeAction,EKeys::Gamepad_LeftTriggerAxis);
 SkiMapping->MapKey(PushAction,EKeys::W);
 SkiMapping->MapKey(PushAction,EKeys::Gamepad_RightTriggerAxis);
 SkiMapping->MapKey(JumpAction,EKeys::SpaceBar); SkiMapping->MapKey(JumpAction,EKeys::Gamepad_FaceButton_Bottom);
 SkiMapping->MapKey(ResetAction,EKeys::R); SkiMapping->MapKey(ResetAction,EKeys::Gamepad_FaceButton_Top);
 SkiMapping->MapKey(LookAction,EKeys::MouseX); SkiMapping->MapKey(LookAction,EKeys::Gamepad_RightX);
 EI->BindAction(SteerAction,ETriggerEvent::Triggered,this,&ASkiPawn::Steer);
 EI->BindAction(SteerAction,ETriggerEvent::Completed,this,&ASkiPawn::Steer);
 EI->BindAction(BrakeAction,ETriggerEvent::Triggered,this,&ASkiPawn::Brake);
 EI->BindAction(BrakeAction,ETriggerEvent::Completed,this,&ASkiPawn::Brake);
 EI->BindAction(PushAction,ETriggerEvent::Triggered,this,&ASkiPawn::Push);
 EI->BindAction(PushAction,ETriggerEvent::Completed,this,&ASkiPawn::Push);
 EI->BindAction(JumpAction,ETriggerEvent::Started,this,&ASkiPawn::Jump);
 EI->BindAction(ResetAction,ETriggerEvent::Started,this,&ASkiPawn::ResetRun);
 EI->BindAction(LookAction,ETriggerEvent::Triggered,this,&ASkiPawn::Look);
 if(auto* PC=Cast<APlayerController>(Controller)) {
  if(auto* LP=PC->GetLocalPlayer()) {
   if(auto* S=LP->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>()) S->AddMappingContext(SkiMapping,0);
  }
 }
 UE_LOG(LogTemp,Display,TEXT("FALLLINE_INPUT_READY keyboard+gamepad mappings=%d"),SkiMapping->GetMappings().Num());
}
void ASkiPawn::Steer(const FInputActionValue& V) {Steering=FMath::Clamp(V.Get<float>(),-1.f,1.f);}
void ASkiPawn::Brake(const FInputActionValue& V) {Braking=FMath::Clamp(V.Get<float>(),0.f,1.f);}
void ASkiPawn::Push(const FInputActionValue& V) {Pushing=FMath::Clamp(V.Get<float>(),0.f,1.f);}
void ASkiPawn::Look(const FInputActionValue& V) {AddControllerYawInput(V.Get<float>());}
void ASkiPawn::Jump() {
 if((bGrounded||bGrinding)&&JumpCooldown<=0) {
  Body->AddImpulse((GroundNormal+FVector::UpVector).GetSafeNormal()*JumpSpeed,NAME_None,true);
  JumpCooldown=.3f; ++JumpCount; bGrounded=false; bGrinding=false;
  UE_LOG(LogTemp,Display,TEXT("FALLLINE_JUMP count=%d"),JumpCount);
 }
}
void ASkiPawn::ResetRun() {
 SetActorLocationAndRotation(FVector(-8500,0,4730),FRotator::ZeroRotator,false,nullptr,ETeleportType::TeleportPhysics);
 Body->SetPhysicsLinearVelocity(FVector::ZeroVector);
 Body->SetPhysicsAngularVelocityInRadians(FVector::ZeroVector);
 Steering=Braking=Pushing=0; JumpCooldown=.3f;
 if(Controller) Controller->SetControlRotation(FRotator(-18,0,0));
}
void ASkiPawn::Tick(float Dt) {
 Super::Tick(Dt); Dt=FMath::Min(Dt,.05f);
 JumpCooldown=FMath::Max(0.f,JumpCooldown-Dt);
 FHitResult Hit;
 FCollisionQueryParams Query(SCENE_QUERY_STAT(SkiGround),false,this);
 const FVector P=GetActorLocation();
 bGrounded=JumpCooldown<=0 && GetWorld()->LineTraceSingleByChannel(Hit,P,P-FVector(0,0,70),ECC_Visibility,Query);
 bGrinding=bGrounded && Hit.GetComponent() && Hit.GetComponent()->ComponentHasTag(TEXT("Grind"));
 if(bGrounded) GroundNormal=Hit.ImpactNormal;
 const FVector V=Body->GetPhysicsLinearVelocity();
 FVector Forward=FVector::VectorPlaneProject(GetActorForwardVector(),GroundNormal).GetSafeNormal();
 FVector Side=FVector::CrossProduct(GroundNormal,Forward).GetSafeNormal();
 if(bGrounded) {
  const float Edge=FMath::Abs(Steering);
  // Directional snow resistance. Side grip increases with edge angle; longitudinal glide stays low.
  const float Grip=FMath::Lerp(FlatGrip,EdgeGrip,Edge);
  FVector A=-Side*FVector::DotProduct(V,Side)*FMath::Min(Grip,.8f/FMath::Max(Dt,.001f));
  A-=Forward*FVector::DotProduct(V,Forward)*(.025f+Braking*2.6f);
  A+=Forward*(Pushing*180.f);
  const float Speed=FVector::DotProduct(V,Forward);
  float YawRate=Steering*FMath::Clamp(FMath::Abs(Speed)/SidecutRadius,.15f,1.5f);
  if(bGrinding) {
   ++GrindFrames;
   const FVector RailForward=Hit.GetComponent()->GetForwardVector();
   const FVector RailSide=FVector::CrossProduct(FVector::UpVector,RailForward).GetSafeNormal();
   const float Offset=FVector::DotProduct(P-Hit.GetComponent()->GetComponentLocation(),RailSide);
   A=-RailSide*(Offset*30.f+FVector::DotProduct(V,RailSide)*10.f);
   YawRate=FMath::Clamp(FMath::FindDeltaAngleDegrees(GetActorRotation().Yaw,RailForward.Rotation().Yaw)*.08f,-2.f,2.f);
  }
  Body->AddForce(A,NAME_None,true);
  Body->SetPhysicsAngularVelocityInRadians(FVector(0,0,YawRate));
 } else Body->SetPhysicsAngularVelocityInRadians(FVector(0,0,Steering*.65f));
 UpdateSkierPose(Dt,V);
 // Chase follows the skis smoothly while retaining player camera yaw offsets.
 if(Controller && FMath::Abs(Steering)>.01f) {
  FRotator C=Controller->GetControlRotation();
  C.Yaw+=FMath::RadiansToDegrees(Body->GetPhysicsAngularVelocityInRadians().Z)*Dt;
  Controller->SetControlRotation(C);
 }
 if(P.Z < -70000 || FMath::Abs(P.Y)>90000 || P.X>170000) ResetRun();
}


void ASkiPawn::UpdateSkierPose(float Dt,const FVector& Velocity) {
 // Project the actual ski heading onto the contact plane. This handles both
 // downhill pitch and cross-slope roll, unlike converting normal pitch alone.
 const FVector Up=bGrounded?GroundNormal:FVector::UpVector;
 const FVector Facing=FVector::VectorPlaneProject(GetActorForwardVector(),Up).GetSafeNormal();
 const FQuat Surface=FRotationMatrix::MakeFromXZ(Facing,Up).ToQuat();
 const FQuat LocalSurface=GetActorQuat().Inverse()*Surface;
 // Visual-only binding height follows the actual snow hit. The rotation-locked
 // Chaos box has substantial support clearance on steep slopes; its centre
 // is not the boot/sole contact. Never move the simulated root.
 if(bGrounded) {
  FHitResult VisualHit;
  FCollisionQueryParams VisualQuery(SCENE_QUERY_STAT(SkierVisualContact),false,this);
  const FVector Centre=GetActorLocation();
  if(GetWorld()->LineTraceSingleByChannel(VisualHit,Centre,Centre-FVector(0,0,200),ECC_Visibility,VisualQuery)) {
   const FVector VisualOrigin=VisualHit.ImpactPoint+GroundNormal*9.f;
   VisualRoot->SetRelativeLocation(GetActorTransform().InverseTransformPosition(VisualOrigin));
  }
 } else VisualRoot->SetRelativeLocation(FVector::ZeroVector);
 const FQuat EdgeLean(FVector::ForwardVector,FMath::DegreesToRadians(-Steering*9.f));
 VisualRoot->SetRelativeRotation(FQuat::Slerp(VisualRoot->GetRelativeRotation().Quaternion(),
  LocalSurface*EdgeLean,1.f-FMath::Exp(-12.f*Dt)));
 VisualSteer=FMath::FInterpTo(VisualSteer,Steering,Dt,9.f);
 if(bGrounded&&!bVisualWasGrounded) {
  LandingCompression=FMath::Clamp(-PreviousVerticalSpeed/1800.f,0.f,1.f);
 }
 bVisualWasGrounded=bGrounded;
 PreviousVerticalSpeed=Velocity.Z;
 LandingCompression=FMath::FInterpTo(LandingCompression,0.f,Dt,6.f);
 const float Speed=Velocity.Size2D();
 const float TargetCrouch=(bGrounded?FMath::Clamp(Speed/2400.f,.16f,.8f):.65f)+LandingCompression*.45f;
 VisualCrouch=FMath::FInterpTo(VisualCrouch,TargetCrouch,Dt,10.f);
 auto* Mesh=Cast<USkeletalMesh>(SkierMesh->GetSkinnedAsset());
 if(!Mesh) return;
 const FReferenceSkeleton& Skeleton=Mesh->GetRefSkeleton();
 const auto& Reference=Skeleton.GetRefBonePose();
 const int32 Count=Reference.Num();
 if(Count==0||SkierMesh->BoneSpaceTransforms.Num()!=Count) return;
 TArray<FTransform> Pose;
 Pose.SetNumUninitialized(Count);
 // Solve in skier coordinates (+X forward), avoiding assumptions about each
 // imported bone's local rotation axis. Manny faces +Y in mesh coordinates.
 const FTransform MeshToSkier(FRotator(0,-90,0));
 for(int32 I=0;I<Count;++I) {
  const int32 Parent=Skeleton.GetParentIndex(I);
  Pose[I]=Parent==INDEX_NONE?Reference[I]*MeshToSkier:Reference[I]*Pose[Parent];
 }
 const TArray<FTransform> RefPose=Pose;
 auto Index=[&](const TCHAR* Name){return Skeleton.FindBoneIndex(FName(Name));};
 auto Descendant=[&](int32 Bone,int32 Ancestor) {
  for(int32 I=Bone;I!=INDEX_NONE;I=Skeleton.GetParentIndex(I)) if(I==Ancestor) return true;
  return false;
 };
 auto MoveBranch=[&](int32 Bone,const FVector& Delta) {
  if(Bone==INDEX_NONE) return;
  for(int32 I=Bone;I<Count;++I) if(Descendant(I,Bone)) Pose[I].AddToTranslation(Delta);
 };
 auto RotateBranch=[&](int32 Bone,const FQuat& Rotation) {
  if(Bone==INDEX_NONE) return;
  const FVector Pivot=Pose[Bone].GetLocation();
  for(int32 I=Bone;I<Count;++I) if(Descendant(I,Bone)) {
   Pose[I].SetLocation(Pivot+Rotation.RotateVector(Pose[I].GetLocation()-Pivot));
   Pose[I].SetRotation((Rotation*Pose[I].GetRotation()).GetNormalized());
  }
 };
 const float Crouch=FMath::Clamp(VisualCrouch,0.f,1.1f);
 MoveBranch(Index(TEXT("pelvis")),FVector(-11.f*Crouch,VisualSteer*-6.f,-34.f*Crouch));
 // Distributed spine flexion keeps the head/shoulders articulated during tuck.
 RotateBranch(Index(TEXT("spine_01")),FQuat(FVector::RightVector,FMath::DegreesToRadians(12.f+16.f*Crouch)));
 RotateBranch(Index(TEXT("spine_03")),FQuat(FVector::RightVector,FMath::DegreesToRadians(8.f*Crouch)));
 RotateBranch(Index(TEXT("spine_04")),FQuat(FVector::ForwardVector,FMath::DegreesToRadians(VisualSteer*-10.f)));
 RotateBranch(Index(TEXT("neck_01")),FQuat(FVector::RightVector,FMath::DegreesToRadians(-12.f*Crouch)));
 // Analytic two-bone IK. Bend hints are in skier space, so knee direction is
 // consistent on left/right limbs despite their mirrored reference bone axes.
 auto SolveLimb=[&](const TCHAR* AName,const TCHAR* BName,const TCHAR* CName,
                    const FVector& Target,const FVector& BendHint,bool bLockEndRotation) {
  const int32 A=Index(AName),B=Index(BName),C=Index(CName);
  if(A==INDEX_NONE||B==INDEX_NONE||C==INDEX_NONE) return;
  const FVector Root=Pose[A].GetLocation();
  const float L1=FVector::Distance(Pose[A].GetLocation(),Pose[B].GetLocation());
  const float L2=FVector::Distance(Pose[B].GetLocation(),Pose[C].GetLocation());
  if(L1<1.f||L2<1.f) return;
  FVector Axis=(Target-Root).GetSafeNormal();
  const float D=FMath::Clamp(float(FVector::Distance(Root,Target)),FMath::Abs(L1-L2)+.1f,L1+L2-.1f);
  FVector Bend=FVector::VectorPlaneProject(BendHint,Axis).GetSafeNormal();
  if(Bend.IsNearlyZero()) Bend=FVector::VectorPlaneProject(FVector::ForwardVector,Axis).GetSafeNormal();
  const float Along=(L1*L1+D*D-L2*L2)/(2.f*D);
  const FVector Joint=Root+Axis*Along+Bend*FMath::Sqrt(FMath::Max(0.f,L1*L1-Along*Along));
  RotateBranch(A,FQuat::FindBetweenNormals((Pose[B].GetLocation()-Root).GetSafeNormal(),(Joint-Root).GetSafeNormal()));
  RotateBranch(B,FQuat::FindBetweenNormals((Pose[C].GetLocation()-Pose[B].GetLocation()).GetSafeNormal(),
   (Root+Axis*D-Pose[B].GetLocation()).GetSafeNormal()));
  if(bLockEndRotation) {
   RotateBranch(C,RefPose[C].GetRotation()*Pose[C].GetRotation().Inverse());
  }
 };
 for(const bool bLeft:{true,false}) {
  const TCHAR* Foot=bLeft?TEXT("foot_l"):TEXT("foot_r");
  const int32 F=Index(Foot);
  if(F!=INDEX_NONE) {
   FVector Anchor=RefPose[F].GetLocation();
   // Match the stance to the actual mannequin, keeping each ski under its boot.
   Anchor.X+=bGrounded?0.f:12.f*Crouch;
   UStaticMeshComponent* Ski=bLeft?LeftSki.Get():RightSki.Get();
   Ski->SetRelativeLocation(FVector(Anchor.X+12.f,Anchor.Y,-9.f));
   Ski->SetRelativeRotation(FRotator(0,bGrounded?(bLeft?-1.f:1.f)*Braking*16.f:0,VisualSteer*-5.f));
   if(bGrounded) {
    FCollisionQueryParams Query(SCENE_QUERY_STAT(SkiVisualFit),false,this);
    auto Ground=[&](const FVector& P,FVector& Hit) {
     FHitResult H;
     if(!GetWorld()->LineTraceSingleByChannel(H,P+FVector(0,0,180),P-FVector(0,0,250),ECC_Visibility,Query)) return false;
     Hit=H.ImpactPoint; return true;
    };
    const FTransform Initial=Ski->GetComponentTransform();
    FVector Heel,Toe,Across;
    if(Ground(Initial.TransformPosition(FVector(-65,0,0)),Heel)
       &&Ground(Initial.TransformPosition(FVector(55,0,0)),Toe)
       &&Ground(Initial.TransformPosition(FVector(-65,8,0)),Across)) {
     const FVector Forward=(Toe-Heel).GetSafeNormal();
     FVector Normal=FVector::CrossProduct(Forward,Across-Heel).GetSafeNormal();
     if(Normal.Z<0) Normal=-Normal;
     if(Normal.Z>.3f) {
      const FQuat Fit=FRotationMatrix::MakeFromXZ(Forward,Normal).ToQuat();
      Ski->SetWorldRotation(Fit);
      const FVector Origin=Heel-Forward*(-65.f);
      Ski->SetWorldLocation(Origin);
      float Lift=-1000.f;
      // Support envelope over the real curved base; do not flatten twin tips.
      bool Valid=true;
      const FTransform FitTransform=Ski->GetComponentTransform();
      for(int32 I=0;I<=24;++I) {
       const float X=-95.f+190.f*I/24.f;
       const float T=FMath::Abs(X)/95.f;
       const float E=FMath::Max(0.f,(FMath::Abs(X)-86.f)/9.f);
       const float W=(4.4f+2.5f*T*T)*FMath::Sqrt(FMath::Max(.012f,1.f-E*E));
       const float Front=FMath::Max(0.f,(X-61.f)/34.f);
       const float Tail=FMath::Max(0.f,(-X-72.f)/23.f);
       const float Z=12.f*Front*Front+4.f*Tail*Tail+.65f*(1.f-T*T)-.7f;
       for(float Side:{-1.f,1.f}) {
        const FVector P=FitTransform.TransformPosition(FVector(X,Side*W,Z));
        FVector Hit;
        if(!Ground(P,Hit)) { Valid=false; break; }
        Lift=FMath::Max(Lift,float(Hit.Z-P.Z));
       }
       if(!Valid) break;
      }
      if(Valid&&FMath::Abs(Lift)<60.f) {
       Ski->AddWorldOffset(FVector(0,0,Lift+.5f));
       // Solve the boot to the fitted binding, not the old body-centred stance.
       Anchor=VisualRoot->GetComponentTransform().InverseTransformPosition(
        Ski->GetComponentTransform().TransformPosition(FVector(-12,0,9)));
      } else Ski->SetWorldTransform(Initial);
     }
    }
   }
   SolveLimb(bLeft?TEXT("thigh_l"):TEXT("thigh_r"),bLeft?TEXT("calf_l"):TEXT("calf_r"),
    Foot,Anchor,FVector(1,0,0),true);

  }
  const float Side=bLeft?-1.f:1.f;
  const FVector Hand(48.f+18.f*Crouch,Side*(33.f-8.f*Crouch),95.f-40.f*Crouch);
  SolveLimb(bLeft?TEXT("upperarm_l"):TEXT("upperarm_r"),bLeft?TEXT("lowerarm_l"):TEXT("lowerarm_r"),
   bLeft?TEXT("hand_l"):TEXT("hand_r"),Hand,FVector(-1,Side*.35f,-.3f),false);
 }
 // Convert back to parent-relative transforms once, then refresh the skin.
 // This updates the full hierarchy including fingers/twist bones, not a set
 // of disconnected world-space limbs.
 for(int32 I=0;I<Count;++I) {
  const int32 Parent=Skeleton.GetParentIndex(I);
  SkierMesh->BoneSpaceTransforms[I]=Pose[I].GetRelativeTransform(Parent==INDEX_NONE?MeshToSkier:Pose[Parent]);
  SkierMesh->BoneSpaceTransforms[I].NormalizeRotation();
 }
 SkierMesh->MarkRefreshTransformDirty();
 SkierMesh->RefreshBoneTransforms();
}
