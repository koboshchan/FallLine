# API references

https://dev.epicgames.com/documentation/unreal-engine/enhanced-input-in-unreal-engine
https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UPrimitiveComponent/AddForce
https://dev.epicgames.com/documentation/unreal-engine/scripting-the-unreal-editor-using-python
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorLoadingAndSavingUtils

Installed authoritative source D:/EpicGames/UE_5.8/Engine and Templates/TP_Blank, Templates/TP_ThirdPerson. Target build settings V7, include order Unreal5_8. InputMappingContext.h MapKey; InputAction.h cumulative scalar actions; PrimitiveComponent.h Chaos forces, velocity, constraints, CCD; FileHelpers.h NewBlankMap and SaveMap.

https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorActorSubsystem

https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/Rotator?application_version=5.8
Python Rotator positional order is roll,pitch,yaw, unlike C++. All population/capture rotations use explicit named arguments.
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/HitResult
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SystemLibrary
Terrain verification reads HitResult.to_tuple impact_point slot5 (native HitResult members are not Python public properties).
