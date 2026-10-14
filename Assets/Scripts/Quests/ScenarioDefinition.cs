using UnityEngine;

// tells the quest manager which event can add progress
public enum ScenarioType
{
    KillEnemies,
    CollectItems,
    SlayBoss
}

// adds scenario definition to the unity asset create menu
[CreateAssetMenu(
    fileName = "NewScenario",
    menuName = "Quests/Scenario Definition")]
// stores gameplay rules and llm facts for one reusable scenario
public class ScenarioDefinition : ScriptableObject
{
    // these headers only group fields in the unity inspector
    [Header("Internal Information")]
    // unique id used for selection requests and logs
    public string scenarioId;

    // event type that adds progress to this scenario
    public ScenarioType scenarioType;

    [Header("Gameplay Rules")]
    // id that must match the needed enemy boss or item
    public string targetId;

    // prefab used when the current scene has no matching target
    public GameObject targetPrefab;

    // scene where this target may appear, empty text allows every scene
    public string targetSceneName;

    // number of matching targets needed to finish the scenario
    [Min(1)] public int requiredAmount = 1;

    // rewards set in unity and never changed by the llm
    [Min(0)] public int experienceReward;
    [Min(0)] public int goldReward;

    [Header("Information for the LLM")]
    // visual facts that help the llm describe the real target
    [TextArea(2, 4)]
    public string targetVisualDescription;

    // real abilities and limits that the llm must follow
    [TextArea(2, 4)]
    public string targetAbilityDescription;

    // real map details used as story context
    [TextArea(2, 4)]
    public string mapDescription;

    // cleans ids and number settings when the asset changes in unity
    private void OnValidate()
    {
        scenarioId = scenarioId?.Trim();
        targetId = targetId?.Trim();
        targetSceneName = targetSceneName?.Trim();
        requiredAmount = Mathf.Max(1, requiredAmount);
        experienceReward = Mathf.Max(0, experienceReward);
        goldReward = Mathf.Max(0, goldReward);
    }

    // checks whether targets may appear in this scene
    // an empty scene name allows targets in every scene
    public bool CanSpawnTargetsInScene(string sceneName)
    {
        return string.IsNullOrWhiteSpace(targetSceneName) ||
               targetSceneName == sceneName;
    }
}
