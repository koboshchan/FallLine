using UnrealBuildTool;
public class FallLineTarget : TargetRules {
 public FallLineTarget(TargetInfo Target) : base(Target) {
  Type=TargetType.Game; DefaultBuildSettings=BuildSettingsVersion.V7;
  IncludeOrderVersion=EngineIncludeOrderVersion.Unreal5_8; ExtraModuleNames.Add("FallLine");
 }
}