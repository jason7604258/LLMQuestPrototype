using System;

// lets unity turn this request object into json
[Serializable]
// stores scenario facts, earlier story context, and writing tone
public class NarrativeGenerationRequest
{
    // default writing style used when no custom tone is set
    public const string DefaultNarrativeTone =
        "Accessible open-air adventure fantasy with a hopeful sense of " +
        "exploration. Show nature reclaiming ancient ruins, quiet mystery, " +
        "and gentle melancholy. Use concise, clear language and vivid " +
        "natural imagery. Keep danger adventurous rather than grim or " +
        "tragic. Avoid archaic wording, dense lore, and modern slang. Do " +
        "not reference or imitate names, characters, or lore from existing " +
        "game franchises. Never invent facts or mechanics beyond the " +
        "supplied scenario data. Vary imagery and display names across " +
        "consecutive scenarios.";

    // unique id used to match a request with its gameplay logs
    public string requestId;

    // selected scenario id and gameplay type
    public string scenarioId;
    public string scenarioType;

    // target id and amount needed to finish the scenario
    public string targetId;
    public int requiredAmount;

    // target and map facts supplied as constraints for narrative generation
    public string targetVisualDescription;
    public string targetAbilityDescription;
    public string mapDescription;

    // earlier story recap and requested writing style
    public string previousStorySummary;
    public string tone;

    // creates a backend request from one scenario asset
    public static NarrativeGenerationRequest FromScenario(
        ScenarioDefinition scenario,
        string previousSummary = "",
        string narrativeTone = DefaultNarrativeTone)
    {
        // stops when there is no scenario to copy
        if (scenario == null)
        {
            throw new ArgumentNullException(nameof(scenario));
        }

        // copies fixed gameplay data into a json friendly object
        return new NarrativeGenerationRequest
        {
            // creates a unique thirty two character request id
            requestId = Guid.NewGuid().ToString("N"),
            scenarioId = scenario.scenarioId,

            // turns the scenario type into text for the backend
            scenarioType = scenario.scenarioType.ToString(),
            targetId = scenario.targetId,
            requiredAmount = scenario.requiredAmount,
            targetVisualDescription = scenario.targetVisualDescription,
            targetAbilityDescription = scenario.targetAbilityDescription,
            mapDescription = scenario.mapDescription,

            // removes extra spaces and replaces null with empty text
            previousStorySummary = previousSummary?.Trim() ?? string.Empty,

            // uses the default tone when the custom tone is empty
            tone = NormalizeTone(narrativeTone)
        };
    }

    // returns a clean custom tone or the default tone
    public static string NormalizeTone(string narrativeTone)
    {
        return string.IsNullOrWhiteSpace(narrativeTone)
            ? DefaultNarrativeTone
            : narrativeTone.Trim();
    }
}
