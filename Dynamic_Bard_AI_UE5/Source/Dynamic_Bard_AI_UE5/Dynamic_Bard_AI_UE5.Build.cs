// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class Dynamic_Bard_AI_UE5 : ModuleRules
{
	public Dynamic_Bard_AI_UE5(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"AIModule",
			"StateTreeModule",
			"GameplayStateTreeModule",
			"UMG",
			"Slate"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { });

		PublicIncludePaths.AddRange(new string[] {
			"Dynamic_Bard_AI_UE5",
			"Dynamic_Bard_AI_UE5/Variant_Platforming",
			"Dynamic_Bard_AI_UE5/Variant_Platforming/Animation",
			"Dynamic_Bard_AI_UE5/Variant_Combat",
			"Dynamic_Bard_AI_UE5/Variant_Combat/AI",
			"Dynamic_Bard_AI_UE5/Variant_Combat/Animation",
			"Dynamic_Bard_AI_UE5/Variant_Combat/Gameplay",
			"Dynamic_Bard_AI_UE5/Variant_Combat/Interfaces",
			"Dynamic_Bard_AI_UE5/Variant_Combat/UI",
			"Dynamic_Bard_AI_UE5/Variant_SideScrolling",
			"Dynamic_Bard_AI_UE5/Variant_SideScrolling/AI",
			"Dynamic_Bard_AI_UE5/Variant_SideScrolling/Gameplay",
			"Dynamic_Bard_AI_UE5/Variant_SideScrolling/Interfaces",
			"Dynamic_Bard_AI_UE5/Variant_SideScrolling/UI"
		});

		// Uncomment if you are using Slate UI
		// PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
