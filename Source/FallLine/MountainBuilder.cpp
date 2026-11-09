#include "MountainBuilder.h"
#include "Engine/World.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Materials/MaterialInterface.h"
#if WITH_EDITOR
#include "Landscape.h"
#include "LandscapeInfo.h"
#include "LandscapeComponent.h"
#endif
AActor* UMountainBuilder::CreateMountain(UObject* WorldContext, UMaterialInterface* SnowMaterial) {
#if WITH_EDITOR
 UWorld* World=WorldContext?WorldContext->GetWorld():nullptr;
 if(!World) return nullptr;
 // Contract checked by PrepareRealDEM.validate_dependencies before map replacement.
 constexpr int32 N=2017;
 constexpr float Spacing=500.f, ZScale=1000.f;
 TArray<uint8> Bytes;
 const FString DEMPath=FPaths::ProjectDir()/TEXT("SourceAssets/DEM/verbier.r16");
 if(!FFileHelper::LoadFileToArray(Bytes,*DEMPath) || Bytes.Num()!=N*N*2) {
  UE_LOG(LogTemp,Error,TEXT("FALLLINE_REAL_DEM_MISSING_OR_INVALID %s"),*DEMPath);
  return nullptr;
 }
 TArray<uint16> Heights; Heights.SetNumUninitialized(N*N);
 for(int32 I=0;I<N*N;++I) Heights[I]=uint16(Bytes[I*2])|(uint16(Bytes[I*2+1])<<8);
 auto* Land=World->SpawnActor<ALandscape>();
 Land->SetActorLabel(TEXT("Verbier SwissALTI3D - Real 10km Alps"));
 Land->SetActorLocation(FVector(-504000,-504000,0));
 Land->SetActorScale3D(FVector(Spacing,Spacing,ZScale));
 Land->LandscapeMaterial=SnowMaterial;
 TMap<FGuid,TArray<uint16>> HeightData; HeightData.Add(FGuid(),MoveTemp(Heights));
 TMap<FGuid,TArray<FLandscapeImportLayerInfo>> Layers; Layers.Add(FGuid(),{});
 Land->Import(FGuid::NewGuid(),0,0,N-1,N-1,1,63,HeightData,nullptr,Layers,ELandscapeImportAlphamapType::Additive,TArrayView<const FLandscapeLayer>());
 Land->CreateLandscapeInfo();
 Land->UpdateAllComponentMaterialInstances();
 Land->MarkPackageDirty();
 UE_LOG(LogTemp,Display,TEXT("FALLLINE_MOUNTAIN_CREATED 2017x2017 10080m SWISSTOPO_REAL_DEM"));
 return Land;
#else
 return nullptr;
#endif
}


// Read-only single sample. Owner polls from Slate with a bounded timeout.
// No compile requests, fallback resolution, material edits or package saves.
#include "Materials/Material.h"
#include "MaterialShared.h"
#include "Materials/MaterialRenderProxy.h"
#include "SceneInterface.h"
#include "RenderingThread.h"
#include "HAL/IConsoleManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
FString UMountainBuilder::ProbeSnowMaterial(UObject* WorldContext, UMaterialInterface* Material)
{
 check(IsInGameThread());
 TSharedRef<FJsonObject> J=MakeShared<FJsonObject>();
 J->SetStringField(TEXT("status"),TEXT("UNVERIFIED"));
 J->SetBoolField(TEXT("readonly"),true);
 UWorld* W=WorldContext?WorldContext->GetWorld():nullptr;
 if(W && W->Scene && Material) {
  const auto FL=W->Scene->GetFeatureLevel();
  const auto Platform=GShaderPlatformForFeatureLevel[FL];
  const auto* QVar=IConsoleManager::Get().FindConsoleVariable(TEXT("r.MaterialQualityLevel"));
  const int32 Q=QVar?QVar->GetInt():-1;
  J->SetStringField(TEXT("material"),Material->GetPathName());
  J->SetNumberField(TEXT("feature_level"),int32(FL));
  J->SetNumberField(TEXT("shader_platform"),int32(Platform));
  J->SetNumberField(TEXT("quality"),Q);
  if(Q>=0 && Q<int32(EMaterialQualityLevel::Num)) {
   const FMaterialResource* R=Material->GetMaterialResource(Platform,EMaterialQualityLevel::Type(Q));
   const bool GT=R && R->GetGameThreadShaderMap() && R->IsGameThreadShaderMapComplete();
   TArray<TSharedPtr<FJsonValue>> Errors;
   if(R) for(const FString& E:R->GetCompileErrors()) Errors.Add(MakeShared<FJsonValueString>(E));
   J->SetBoolField(TEXT("gt_resource"),R!=nullptr);
   J->SetBoolField(TEXT("gt_shader_map"),R && R->GetGameThreadShaderMap()!=nullptr);
   J->SetBoolField(TEXT("gt_complete"),GT);
   J->SetArrayField(TEXT("compile_errors"),Errors);
   const FMaterialRenderProxy* Proxy=Material->GetRenderProxy();
   bool RTResource=false,RTComplete=false;
   ENQUEUE_RENDER_COMMAND(FallLineReadOnlySnowProbe)(
    [Proxy,FL,&RTResource,&RTComplete](FRHICommandListImmediate&) {
     const FMaterial* Actual=Proxy?Proxy->GetMaterialNoFallback(FL):nullptr;
     RTResource=Actual!=nullptr;
     RTComplete=Actual && Actual->IsRenderingThreadShaderMapComplete();
    });
   FlushRenderingCommands();
   J->SetBoolField(TEXT("rt_no_fallback_resource"),RTResource);
   J->SetBoolField(TEXT("rt_complete"),RTComplete);
   if(GT && Errors.IsEmpty() && RTResource && RTComplete) J->SetStringField(TEXT("status"),TEXT("PASS"));
  }
 }
 FString Result;
 const TSharedRef<TJsonWriter<>> Writer=TJsonWriterFactory<>::Create(&Result);
 FJsonSerializer::Serialize(J,Writer);
 return Result;
}
