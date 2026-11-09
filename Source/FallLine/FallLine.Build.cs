using UnrealBuildTool;
public class FallLine : ModuleRules {
 public FallLine(ReadOnlyTargetRules Target) : base(Target) {
  PCHUsage=PCHUsageMode.UseExplicitOrSharedPCHs;
  PrivateDependencyModuleNames.AddRange(new [] {"RenderCore","RHI","Json"});
  PublicDependencyModuleNames.AddRange(new [] {"Core","CoreUObject","Engine","InputCore","EnhancedInput","PhysicsCore","Landscape"});
 }
}