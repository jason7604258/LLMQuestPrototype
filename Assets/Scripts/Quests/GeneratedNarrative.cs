using System;

// lets unity turn backend json into this object
[Serializable]
// stores story text from the backend or a local fallback
// the active scenario still controls all gameplay rules
public class GeneratedNarrative
{
    // text shown as the quest title and opening story
    public string title;
    public string introduction;

    // objective returned by the llm, unity checks its amount before use
    public string objectiveText;

    // target names used for one target or many targets
    public string targetDisplayNameSingular;
    public string targetDisplayNamePlural;

    // text shown after the player finishes the scenario
    public string completionText;

    // short story recap sent with the next request
    public string storySummary;
}
