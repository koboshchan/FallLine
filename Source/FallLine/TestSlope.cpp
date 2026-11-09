#include "TestSlope.h"
#include "Components/StaticMeshComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/VolumetricCloudComponent.h"
#include "Components/PostProcessComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"

ATestSlope::ATestSlope() {
 auto* Root=CreateDefaultSubobject<USceneComponent>(TEXT("SlopeRoot"));
 SetRootComponent(Root);
 static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
 static ConstructorHelpers::FObjectFinder<UMaterialInterface> White(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
 auto Block=[&](const TCHAR* Name,FVector P,FVector Scale,FRotator R,bool Grind) {
  auto* C=CreateDefaultSubobject<UStaticMeshComponent>(Name);
  C->SetupAttachment(Root); C->SetStaticMesh(Cube.Object);
  C->SetMaterial(0,White.Object); C->SetRelativeLocation(P);
  C->SetRelativeScale3D(Scale); C->SetRelativeRotation(R);
  C->SetCollisionProfileName(TEXT("BlockAll"));
  if(Grind) C->ComponentTags.Add(TEXT("Grind"));
  return C;
 };
 const FRotator Downhill(-14,0,0);
 // Features follow the slope fall line. Narrow rail and wider box are grind-tagged.
 auto Height=[](float X){return 2500.f-X*FMath::Tan(FMath::DegreesToRadians(14.f))+50.f;};
 Block(TEXT("Rail"),FVector(-2500,-700,Height(-2500)+55),FVector(18,.18,.22),Downhill,true);
 Block(TEXT("Box"),FVector(1000,700,Height(1000)+38),FVector(22,2.4,.7),Downhill,true);
 Block(TEXT("RailEntry"),FVector(-3650,-700,Height(-3650)+8),FVector(5,2,.35),FRotator(0,0,0),false);
 Block(TEXT("BoxEntry"),FVector(-350,700,Height(-350)+6),FVector(5,3,.35),FRotator(-4,0,0),false);
 auto* Sun=CreateDefaultSubobject<UDirectionalLightComponent>(TEXT("Sun"));
 Sun->SetupAttachment(Root); Sun->SetRelativeRotation(FRotator(-35,-35,0)); Sun->SetIntensity(65000); Sun->bAtmosphereSunLight=true; Sun->SetLightColor(FLinearColor(1.f,.94f,.84f));
 auto* Sky=CreateDefaultSubobject<USkyLightComponent>(TEXT("SkyFill"));
 Sky->SetupAttachment(Root); Sky->SetIntensity(1); Sky->bRealTimeCapture=true;
 auto* Atmosphere=CreateDefaultSubobject<USkyAtmosphereComponent>(TEXT("Atmosphere"));
 Atmosphere->SetupAttachment(Root);
 auto* Exposure=CreateDefaultSubobject<UPostProcessComponent>(TEXT("MountainExposure"));
 Exposure->SetupAttachment(Root); Exposure->bUnbound=true;
 Exposure->Settings.bOverride_AutoExposureMinBrightness=true;
 Exposure->Settings.bOverride_AutoExposureMaxBrightness=true;
 Exposure->Settings.AutoExposureMinBrightness=12.f;
 Exposure->Settings.AutoExposureMaxBrightness=15.f;
 Exposure->Settings.bOverride_AutoExposureBias=true;
 Exposure->Settings.AutoExposureBias=.5f;
 auto* Fog=CreateDefaultSubobject<UExponentialHeightFogComponent>(TEXT("ValleyMist"));
 Fog->SetupAttachment(Root); Fog->SetFogDensity(.006f); Fog->bEnableVolumetricFog=true;
 auto* Clouds=CreateDefaultSubobject<UVolumetricCloudComponent>(TEXT("AlpineClouds"));
 Clouds->SetupAttachment(Root); Clouds->LayerBottomAltitude=3.2f; Clouds->LayerHeight=5;
 static ConstructorHelpers::FObjectFinder<UMaterialInterface> CloudMat(TEXT("/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst.m_SimpleVolumetricCloud_Inst"));
 if(CloudMat.Succeeded()) Clouds->SetMaterial(CloudMat.Object);
}
