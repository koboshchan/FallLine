#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MountainBuilder.generated.h"
UCLASS()
class FALLLINE_API UMountainBuilder : public UBlueprintFunctionLibrary {
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="Fall Line|Editor")
 static FString ProbeSnowMaterial(UObject* WorldContext, UMaterialInterface* Material);
 UFUNCTION(BlueprintCallable,Category="Fall Line|Editor")
 static AActor* CreateMountain(UObject* WorldContext, UMaterialInterface* SnowMaterial);
};
