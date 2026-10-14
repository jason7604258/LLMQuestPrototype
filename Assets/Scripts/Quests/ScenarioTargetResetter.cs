using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

// prevents two target resetters on the same gameobject
[DisallowMultipleComponent]
// saves target templates and creates fresh targets for each scenario
public class ScenarioTargetResetter : MonoBehaviour
{
    // stores everything needed to recreate one scene target
    private sealed class TargetTemplate
    {
        // hidden inactive copy used as the source for new targets
        public GameObject template;

        // original name and quest ids used when matching a scenario
        public string originalName;
        public string enemyId;
        public string bossId;
        public string itemId;

        // original transform values used for each new target
        public Vector3 worldPosition;
        public Quaternion worldRotation;
        public Vector3 localScale;
    }

    // target copies and useful spawn points captured from the loaded scene
    private readonly List<TargetTemplate> templates =
        new List<TargetTemplate>();
    private readonly List<Vector3> sceneSpawnPositions =
        new List<Vector3>();

    // hidden template holder and visible runtime target holder
    private Transform templateRoot;
    private Transform runtimeTargetRoot;

    // captures targets already present in the first loaded scene
    private void Awake()
    {
        CaptureSceneTargets(SceneManager.GetActiveScene());
    }

    // listens for later scene loads without adding the callback twice
    private void OnEnable()
    {
        SceneManager.sceneLoaded -= HandleSceneLoaded;
        SceneManager.sceneLoaded += HandleSceneLoaded;
    }

    // stops listening while this component is disabled
    private void OnDisable()
    {
        SceneManager.sceneLoaded -= HandleSceneLoaded;
    }

    // captures the new scene and restores targets for an active quest
    private void HandleSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        CaptureSceneTargets(scene);

        // only resets targets when an unfinished quest already exists
        QuestManager questManager = QuestManager.Instance;
        if (questManager != null &&
            questManager.IsQuestActive &&
            questManager.ActiveScenario != null)
        {
            // creates only the amount still needed after travel to this scene
            int remainingAmount = Mathf.Max(
                1,
                questManager.ActiveScenario.requiredAmount -
                questManager.CurrentProgress);
            // scene reload failures are logged without opening the retry control
            ResetTargetsForScenario(
                questManager.ActiveScenario,
                remainingAmount,
                scene);
        }
    }

    // prepares the full target count or defers spawning to the permitted scene
    public bool ResetTargetsForScenario(ScenarioDefinition scenario)
    {
        return ResetTargetsForScenario(
            scenario,
            scenario != null ? scenario.requiredAmount : 0,
            SceneManager.GetActiveScene());
    }

    // clears old matching targets and creates the requested amount
    private bool ResetTargetsForScenario(
        ScenarioDefinition scenario,
        int spawnAmount,
        Scene targetScene)
    {
        // rejects missing scenario data or an invalid amount
        if (scenario == null || spawnAmount <= 0)
        {
            Debug.LogError(
                "Cannot reset targets for an invalid scenario.",
                this);
            return false;
        }

        // keeps targets out of scenes where they do not belong
        if (!scenario.CanSpawnTargetsInScene(targetScene.name))
        {
            DestroyRuntimeTargets();
            Debug.Log(
                $"Scenario '{scenario.scenarioId}' is active, but its " +
                $"targets belong to scene '{scenario.targetSceneName}'. " +
                $"No targets were spawned in '{targetScene.name}'.",
                this);
            return true;
        }

        // finds templates with the required target id and scenario type
        List<TargetTemplate> matchingTemplates =
            FindMatchingTemplates(scenario);

        // stops when neither a scene template nor a prefab can make targets
        if (matchingTemplates.Count == 0 && scenario.targetPrefab == null)
        {
            Debug.LogError(
                $"Scenario '{scenario.scenarioId}' target " +
                $"'{scenario.targetId}' has neither a current-scene " +
                "template nor a global target prefab.",
                this);
            return false;
        }

        // removes old targets before building one clean scenario set
        DestroyRuntimeTargets();
        DestroyCurrentTargets(scenario, targetScene);
        CreateRuntimeTargetRoot(targetScene);

        // repeats captured templates when the scenario needs more targets
        for (int index = 0; index < spawnAmount; index++)
        {
            if (matchingTemplates.Count > 0)
            {
                TargetTemplate targetTemplate =
                    matchingTemplates[index % matchingTemplates.Count];
                SpawnTarget(
                    targetTemplate,
                    index / matchingTemplates.Count);
            }
            // uses the scenario prefab when no matching scene target exists
            else
            {
                SpawnTargetPrefab(scenario.targetPrefab, index);
            }
        }

        Debug.Log(
            $"Reset {spawnAmount} gameplay target(s) for scenario " +
            $"'{scenario.scenarioId}' in scene " +
            $"'{targetScene.name}'.",
            this);
        return true;
    }

    // checks whether the current scene can supply this scenario target
    public bool HasTargetTemplateForScenario(ScenarioDefinition scenario)
    {
        return scenario != null &&
               scenario.requiredAmount > 0 &&
               !string.IsNullOrWhiteSpace(scenario.targetId) &&
               scenario.CanSpawnTargetsInScene(
                   SceneManager.GetActiveScene().name) &&
               (FindMatchingTemplates(scenario).Count > 0 ||
                scenario.targetPrefab != null);
    }

    // saves inactive copies of all quest enemies bosses and loot in a scene
    private void CaptureSceneTargets(Scene scene)
    {
        // clears data from the earlier scene before scanning the new one
        templates.Clear();
        sceneSpawnPositions.Clear();
        runtimeTargetRoot = null;
        if (templateRoot != null)
        {
            Destroy(templateRoot.gameObject);
        }

        // creates a hidden inactive holder so templates never join gameplay
        GameObject rootObject = new GameObject("ScenarioTargetTemplates");
        rootObject.hideFlags = HideFlags.HideInHierarchy | HideFlags.DontSave;
        rootObject.transform.SetParent(transform, false);
        rootObject.SetActive(false);
        templateRoot = rootObject.transform;

        // collects active quest targets from every root in the supplied scene
        List<Enemy_Health> enemies = new List<Enemy_Health>();
        List<Loot> lootObjects = new List<Loot>();

        if (scene.IsValid() && scene.isLoaded)
        {
            foreach (GameObject sceneRoot in scene.GetRootGameObjects())
            {
                enemies.AddRange(
                    sceneRoot.GetComponentsInChildren<Enemy_Health>(false));
                lootObjects.AddRange(
                    sceneRoot.GetComponentsInChildren<Loot>(false));
            }
        }

        // saves enemies and bosses that have a quest id
        foreach (Enemy_Health enemy in enemies)
        {
            if (enemy == null ||
                (string.IsNullOrWhiteSpace(enemy.EnemyId) &&
                 string.IsNullOrWhiteSpace(enemy.BossId)))
            {
                continue;
            }

            templates.Add(CreateTemplate(
                enemy.gameObject,
                enemy.EnemyId,
                enemy.BossId,
                string.Empty));
            AddSceneSpawnPosition(enemy.transform.position);
        }

        // saves loot that is allowed to add quest progress
        foreach (Loot loot in lootObjects)
        {
            string itemId = loot?.Item?.ItemId;
            if (loot == null ||
                !loot.CountsForQuestProgress ||
                string.IsNullOrWhiteSpace(itemId))
            {
                continue;
            }

            templates.Add(CreateTemplate(
                loot.gameObject,
                string.Empty,
                string.Empty,
                itemId));
            AddSceneSpawnPosition(loot.transform.position);
        }

        Debug.Log(
            $"Captured {templates.Count} fixed target template(s) from " +
            $"scene '{scene.name}'.",
            this);
    }

    // makes one hidden target copy and stores its matching data
    private TargetTemplate CreateTemplate(
        GameObject source,
        string enemyId,
        string bossId,
        string itemId)
    {
        Transform sourceTransform = source.transform;
        GameObject template = Instantiate(source, templateRoot);
        template.name = $"{source.name}_QuestTemplate";

        return new TargetTemplate
        {
            template = template,
            originalName = source.name,
            enemyId = enemyId?.Trim() ?? string.Empty,
            bossId = bossId?.Trim() ?? string.Empty,
            itemId = itemId?.Trim() ?? string.Empty,
            worldPosition = sourceTransform.position,
            worldRotation = sourceTransform.rotation,
            localScale = sourceTransform.localScale
        };
    }

    // returns saved templates with the same target id and scenario type
    private List<TargetTemplate> FindMatchingTemplates(
        ScenarioDefinition scenario)
    {
        List<TargetTemplate> matches = new List<TargetTemplate>();

        foreach (TargetTemplate targetTemplate in templates)
        {
            // checks the id field used by this scenario type
            bool isMatch;
            switch (scenario.scenarioType)
            {
                case ScenarioType.CollectItems:
                    isMatch = targetTemplate.itemId == scenario.targetId;
                    break;

                case ScenarioType.SlayBoss:
                    isMatch = targetTemplate.bossId == scenario.targetId;
                    break;

                case ScenarioType.KillEnemies:
                default:
                    isMatch =
                        string.IsNullOrWhiteSpace(targetTemplate.bossId) &&
                        targetTemplate.enemyId == scenario.targetId;
                    break;
            }

            if (isMatch)
            {
                matches.Add(targetTemplate);
            }
        }

        return matches;
    }

    // removes active scene targets that belong to the selected scenario
    private void DestroyCurrentTargets(
        ScenarioDefinition scenario,
        Scene activeScene)
    {
        // collection scenarios search active loot by item id
        if (scenario.scenarioType == ScenarioType.CollectItems)
        {
            Loot[] lootObjects = FindObjectsByType<Loot>(
                FindObjectsInactive.Exclude);
            foreach (Loot loot in lootObjects)
            {
                if (loot != null &&
                    loot.gameObject.scene == activeScene &&
                    loot.CountsForQuestProgress &&
                    loot.Item?.ItemId == scenario.targetId)
                {
                    Destroy(loot.gameObject);
                }
            }

            return;
        }

        // combat scenarios search active enemies by enemy or boss id
        Enemy_Health[] enemies = FindObjectsByType<Enemy_Health>(
            FindObjectsInactive.Exclude);

        foreach (Enemy_Health enemy in enemies)
        {
            if (enemy == null)
            {
                continue;
            }

            if (enemy.gameObject.scene != activeScene)
            {
                continue;
            }

            // boss scenarios use boss id and normal combat uses enemy id
            bool isMatch = scenario.scenarioType == ScenarioType.SlayBoss
                ? enemy.BossId == scenario.targetId
                : enemy.EnemyId == scenario.targetId;
            if (isMatch)
            {
                Destroy(enemy.gameObject);
            }
        }
    }

    // creates one target from a captured scene template
    private void SpawnTarget(TargetTemplate targetTemplate, int repeatIndex)
    {
        GameObject instance = Instantiate(
            targetTemplate.template,
            targetTemplate.worldPosition +
            new Vector3(repeatIndex * 0.75f, 0f, 0f),
            targetTemplate.worldRotation,
            runtimeTargetRoot);
        instance.name = targetTemplate.originalName;
        instance.transform.localScale = targetTemplate.localScale;
        instance.SetActive(true);
    }

    // creates one target from the fallback prefab
    private void SpawnTargetPrefab(GameObject targetPrefab, int spawnIndex)
    {
        GameObject instance = Instantiate(
            targetPrefab,
            GetSpawnPosition(spawnIndex),
            targetPrefab.transform.rotation,
            runtimeTargetRoot);
        instance.name = targetPrefab.name;
        instance.transform.localScale = targetPrefab.transform.localScale;
        instance.SetActive(true);
    }

    // creates a scene object that holds all targets made for this scenario
    private void CreateRuntimeTargetRoot(Scene scene)
    {
        GameObject rootObject = new GameObject("ActiveScenarioTargets");
        SceneManager.MoveGameObjectToScene(
            rootObject,
            scene);
        runtimeTargetRoot = rootObject.transform;
    }

    // removes the target group made for the earlier scenario
    private void DestroyRuntimeTargets()
    {
        if (runtimeTargetRoot == null)
        {
            return;
        }

        Destroy(runtimeTargetRoot.gameObject);
        runtimeTargetRoot = null;
    }

    // stores one spawn point while skipping nearly equal positions
    private void AddSceneSpawnPosition(Vector3 position)
    {
        foreach (Vector3 existingPosition in sceneSpawnPositions)
        {
            if ((existingPosition - position).sqrMagnitude < 0.01f)
            {
                return;
            }
        }

        sceneSpawnPositions.Add(position);
    }

    // chooses a prefab position from saved points or a player offset
    private Vector3 GetSpawnPosition(int spawnIndex)
    {
        // places targets near the player when the scene has no saved positions
        if (sceneSpawnPositions.Count == 0)
        {
            GameObject player = GameObject.FindGameObjectWithTag("Player");
            Vector3 origin = player != null ? player.transform.position : Vector3.zero;
            return origin + new Vector3(2f + spawnIndex, 2f, 0f);
        }

        // spreads repeated targets around saved scene positions
        Vector3 basePosition =
            sceneSpawnPositions[spawnIndex % sceneSpawnPositions.Count];
        int repeatIndex = spawnIndex / sceneSpawnPositions.Count;
        float horizontalOffset = spawnIndex % 2 == 0 ? 1.25f : -1.25f;
        return basePosition + new Vector3(
            horizontalOffset + repeatIndex * 0.75f,
            1.25f,
            0f);
    }
}
