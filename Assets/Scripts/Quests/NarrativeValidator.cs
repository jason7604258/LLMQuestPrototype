using System.Text.RegularExpressions;

// checks story text before the quest system uses it
// this helper stores no data and needs no gameobject
public static class NarrativeValidator
{
    // text limits keep content readable in the quest ui
    private const int MaximumTitleLength = 80;
    private const int MaximumIntroductionLength = 500;
    private const int MaximumObjectiveLength = 160;
    private const int MaximumTargetNameLength = 60;
    private const int MaximumCompletionLength = 300;
    private const int MaximumStorySummaryLength = 300;

    // checks every story field and returns the first problem
    public static bool TryValidate(
        GeneratedNarrative narrative,
        ScenarioDefinition scenario,
        out string validationError)
    {
        // both story text and scenario rules are required
        if (narrative == null)
        {
            validationError = "Narrative is null.";
            return false;
        }

        if (scenario == null)
        {
            validationError = "Scenario is null.";
            return false;
        }

        // each field needs visible text within its size limit
        // this check stops at the first bad field
        if (!IsValidText(
                narrative.title,
                "title",
                MaximumTitleLength,
                out validationError) ||
            !IsValidText(
                narrative.introduction,
                "introduction",
                MaximumIntroductionLength,
                out validationError) ||
            !IsValidText(
                narrative.objectiveText,
                "objectiveText",
                MaximumObjectiveLength,
                out validationError) ||
            !IsValidText(
                narrative.targetDisplayNameSingular,
                "targetDisplayNameSingular",
                MaximumTargetNameLength,
                out validationError) ||
            !IsValidText(
                narrative.targetDisplayNamePlural,
                "targetDisplayNamePlural",
                MaximumTargetNameLength,
                out validationError) ||
            !IsValidText(
                narrative.completionText,
                "completionText",
                MaximumCompletionLength,
                out validationError) ||
            !IsValidText(
                narrative.storySummary,
                "storySummary",
                MaximumStorySummaryLength,
                out validationError))
        {
            return false;
        }

        // builds a pattern that finds only the exact required amount
        string requiredAmount = scenario.requiredAmount.ToString();
        string exactAmountPattern =
            $@"(?<!\d){Regex.Escape(requiredAmount)}(?!\d)";

        // rejects an objective that does not contain the required numeric token
        if (!Regex.IsMatch(narrative.objectiveText, exactAmountPattern))
        {
            validationError =
                $"objectiveText must contain the exact required amount " +
                $"{scenario.requiredAmount}.";
            return false;
        }

        // clears the error when every check passes
        validationError = string.Empty;
        return true;
    }

    // checks one text field for content and length
    private static bool IsValidText(
        string value,
        string fieldName,
        int maximumLength,
        out string validationError)
    {
        // rejects missing or blank text
        if (string.IsNullOrWhiteSpace(value))
        {
            validationError = $"{fieldName} must not be empty.";
            return false;
        }

        // ignores extra spaces at the start and end
        if (value.Trim().Length > maximumLength)
        {
            validationError =
                $"{fieldName} exceeds {maximumLength} characters.";
            return false;
        }

        // clears the error when both checks pass
        validationError = string.Empty;
        return true;
    }
}
