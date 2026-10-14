using UnityEngine;

// prevents two fallback providers on the same gameobject
[DisallowMultipleComponent]
// creates local story text when backend text cannot be used
// this is a runtime safety feature even though its name includes test
public class NarrativeTestProvider : MonoBehaviour
{
    // chooses fallback text that matches the scenario type and target
    public GeneratedNarrative GenerateTestNarrative(
        ScenarioDefinition scenario)
    {
        // stops when no scenario was supplied
        if (scenario == null)
        {
            throw new System.ArgumentNullException(nameof(scenario));
        }

        // sends each scenario type to its matching text builder
        switch (scenario.scenarioType)
        {
            case ScenarioType.CollectItems:
                return GenerateCollectNarrative(
                    scenario.requiredAmount,
                    GetLocationDescription(scenario));

            case ScenarioType.SlayBoss:
                return GenerateBossNarrative(
                    scenario.requiredAmount,
                    GetLocationDescription(scenario));

            case ScenarioType.KillEnemies:
                return GenerateKillNarrative(scenario);

            default:
                throw new System.ArgumentOutOfRangeException(
                    nameof(scenario.scenarioType),
                    scenario.scenarioType,
                    "Unsupported scenario type.");
        }
    }

    // builds fallback text for the torch guard target
    private static GeneratedNarrative GenerateTorchNarrative(
        int amount,
        string location)
    {
        string displayName = amount == 1 ? "Torch Guard" : "Torch Guards";
        return new GeneratedNarrative
        {
            title = "Torches on the Old Road",
            introduction =
                $"{amount} {displayName} patrol the {location}, blocking " +
                "a path once used by travelers.",
            objectiveText = $"Defeat {amount} {displayName}.",
            targetDisplayNameSingular = "Torch Guard",
            targetDisplayNamePlural = "Torch Guards",
            completionText =
                "The road is peaceful again, and warm torchlight fades " +
                "beneath the open sky.",
            storySummary =
                $"The player defeated {amount} {displayName} in the " +
                $"{location}, reopening the old road to travelers."
        };
    }

    // builds fallback text for normal enemy targets
    // display names change story text but never change the target id
    private static GeneratedNarrative GenerateKillNarrative(
        ScenarioDefinition scenario)
    {
        int amount = Mathf.Max(1, scenario.requiredAmount);
        if (scenario.targetId == "enemy_torch")
        {
            return GenerateTorchNarrative(
                amount,
                GetLocationDescription(scenario));
        }

        string title;
        string singular;
        string plural;
        string omen;

        switch (scenario.targetId)
        {
            case "enemy_caveborn_bear":
                title = "Claw Marks by the Old Road";
                singular = "Caveborn Bear";
                plural = "Caveborn Bears";
                omen = "fresh claw marks beside an overgrown path";
                break;

            case "enemy_caveborn_lizard":
                title = "Bright Crests in the Grass";
                singular = "Caveborn Lizard";
                plural = "Caveborn Lizards";
                omen = "bright crests moving above the tall grass";
                break;

            case "enemy_caveborn_spider":
                title = "Webs Between the Ruins";
                singular = "Caveborn Spider";
                plural = "Caveborn Spiders";
                omen = "silver webs stretched between broken stones";
                break;

            case "enemy_caveborn_snake":
                title = "Tracks in the Warm Grass";
                singular = "Caveborn Snake";
                plural = "Caveborn Snakes";
                omen = "orange bands flashing through the warm grass";
                break;

            case "enemy_caveborn_turtle":
                title = "The Shell Beside the Ruins";
                singular = "Caveborn Turtle";
                plural = "Caveborn Turtles";
                omen = "a spiral marked shell weathered like the old stones";
                break;

            default:
                title = "Creatures on the Old Road";
                singular = "Wild Creature";
                plural = "Wild Creatures";
                omen = "fresh tracks scattered along the overgrown road";
                break;
        }

        string displayName = amount == 1 ? singular : plural;
        string moveVerb = amount == 1 ? "moves" : "move";
        string location = GetLocationDescription(scenario);
        return new GeneratedNarrative
        {
            title = title,
            introduction =
                $"{amount} {displayName} {moveVerb} through the {location}. " +
                $"Look for {omen}.",
            objectiveText = $"Defeat {amount} {displayName}.",
            targetDisplayNameSingular = singular,
            targetDisplayNamePlural = plural,
            completionText =
                "The path is safe again. Wind moves through the leaves, " +
                "and the old road opens ahead.",
            storySummary =
                $"The player defeated {amount} {displayName} in the " +
                $"{location}, making the old road safe again."
        };
    }

    // builds fallback text for item collection
    private static GeneratedNarrative GenerateCollectNarrative(
        int amount,
        string location)
    {
        return new GeneratedNarrative
        {
            title = "Glowcaps Among the Grass",
            introduction =
                $"Pale mushrooms glow softly among the grass and broken " +
                $"stones of the {location}. Gather them while their spores " +
                "shine in the morning light.",
            objectiveText = $"Gather {amount} Glowcap Mushrooms.",
            targetDisplayNameSingular = "Glowcap Mushroom",
            targetDisplayNamePlural = "Glowcap Mushrooms",
            completionText =
                "The last glowcap is gathered. A few bright spores drift " +
                "over the grass and disappear into the open air.",
            storySummary =
                $"The player gathered {amount} Glowcap Mushrooms from the " +
                $"{location}, following their light among the old stones."
        };
    }

    // builds fallback text for the boss scenario
    private static GeneratedNarrative GenerateBossNarrative(
        int amount,
        string location)
    {
        return new GeneratedNarrative
        {
            title = "The Guardian of the Mountain Arena",
            introduction =
                $"An armoured Torch Warden patrols the {location}, where " +
                "grass grows between old stones beneath the open sky.",
            objectiveText = $"Defeat {amount} Torch Warden.",
            targetDisplayNameSingular = "Torch Warden",
            targetDisplayNamePlural = "Torch Wardens",
            completionText =
                "The arena grows quiet. Sunlight reaches the old path, " +
                "and the mountain wind moves freely again.",
            storySummary =
                $"The player defeated {amount} Torch Warden in the " +
                $"{location}, leaving the mountain path peaceful again."
        };
    }

    // changes a unity scene name into natural story wording
    // unknown scenes use a simple safe description
    private static string GetLocationDescription(
        ScenarioDefinition scenario)
    {
        switch (scenario?.targetSceneName)
        {
            case "Forest":
                return "ruined forest settlement";

            case "Arena":
                return "abandoned mountain arena";

            default:
                return "weathered ruins";
        }
    }
}
