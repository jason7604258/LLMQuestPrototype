using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// starts quest setup before normal gameplay components
[DefaultExecutionOrder(-70)]
// prevents two quest managers on the same gameobject
[DisallowMultipleComponent]
// manages the complete quest flow
// selects the scenario, requests and checks story text, prepares targets, tracks progress, gives rewards, updates ui, and saves logs
// scenario data controls gameplay rules
// narrative data controls only the text shown to the player
// the llm can write story text, but it cannot change gameplay
// python backend fallback follows the backend success path
// unity narrative fallback is recorded as local_fallback
public class QuestManager : MonoBehaviour
{
    // shared quest manager used by other gameplay components
    public static QuestManager Instance { get; private set; }

    // key used to save the latest story recap for the current tone
    private const string StoryHistoryPlayerPrefsKey =
        "LLMQuest.LastCompletedStorySummary.OpenAirV1";

    // older save key removed when story history is cleared
    private const string LegacyStoryHistoryPlayerPrefsKey =
        "LLMQuest.LastCompletedStorySummary";

    // same tone size limit used by the backend
    private const int MaximumBackendToneLength = 1000;

    [Header("Scenario")]
    // selected scenario that controls story and gameplay rules
    [SerializeField] private ScenarioDefinition activeScenario;

    // scenario choices used by the random cycle
    [SerializeField] private ScenarioDefinition[] availableScenarios;

    // chooses random scenarios or the scenario set in the inspector
    [SerializeField] private bool randomizeScenarioOnStart = true;

    // avoids the same scenario at the end and start of two cycles
    [SerializeField] private bool avoidImmediateRepeat = true;

    // prepares enemies bosses or items before gameplay starts
    [SerializeField] private ScenarioTargetResetter targetResetter;

    [Header("Automatic Loop")]
    [Tooltip("Automatically generates the first scenario and continues after every completion.")]
    // starts the first and later scenarios without a button click
    [SerializeField] private bool automaticallyRunScenarioLoop = true;
    [Tooltip("Shows Start/Next controls for development. Retry is always shown after a total generation failure.")]
    // shows manual controls during development while keeping retry available
    [SerializeField] private bool showManualControlsInDevelopment;

    [Header("Narrative")]
    // provides fixed local story text when backend text cannot be used
    [SerializeField] private NarrativeTestProvider narrativeProvider;

    // sends story requests and gameplay logs to the backend
    [SerializeField] private NarrativeApiClient narrativeApiClient;

    // writing style sent with every backend story request
    [TextArea(5, 9)]
    [SerializeField] private string narrativeTone =
        NarrativeGenerationRequest.DefaultNarrativeTone;

    // controls whether story history is saved between play sessions
    [SerializeField] private bool persistNarrativeHistory = true;

    [Header("UI")]
    // quest labels and button that may change after a scene load
    [SerializeField] private TMP_Text titleText;
    [SerializeField] private TMP_Text introductionText;
    [SerializeField] private TMP_Text objectiveText;
    [SerializeField] private TMP_Text progressText;
    [SerializeField] private TMP_Text completionText;
    [SerializeField] private Button startButton;
    [SerializeField] private TMP_Text startButtonLabel;

    // accepted story text for the current quest
    private GeneratedNarrative activeNarrative;

    // progress taken only from real gameplay events
    private int currentProgress;

    // current quest and story request states
    private bool questActive;
    private bool questCompleted;
    private bool narrativeRequestInProgress;
    private bool narrativeGenerationFailed;

    // keeps the failed scenario ready for retry
    private bool retrySelectedScenario;

    // request id allowed to change the current quest state
    private string currentNarrativeRequestId = string.Empty;

    // latest story generation error shown in logs
    private string lastNarrativeGenerationError = string.Empty;

    // latest completed story recap sent with the next request
    private string previousStorySummary = string.Empty;

    // last random choice used to avoid an immediate repeat
    private string lastSelectedScenarioId = string.Empty;

    // shuffled scenario list where each choice appears once per cycle
    private readonly List<ScenarioDefinition> scenarioBag =
        new List<ScenarioDefinition>();

    // time when the scenario starts after story acceptance and preparation checks
    private float activeScenarioStartedAt;

    // story source and fallback details saved in gameplay logs
    private string activeNarrativeSource = string.Empty;
    private bool backendNarrativeAcceptedByUnity;
    private string activeUnityValidationError = string.Empty;
    private string activeFallbackReason = string.Empty;

    // tells ui listeners when an important quest state changes
    public event System.Action QuestStateChanged;

    // lets other components read current quest data and state
    public ScenarioDefinition ActiveScenario => activeScenario;
    public GeneratedNarrative ActiveNarrative => activeNarrative;
    public int CurrentProgress => currentProgress;
    public bool IsQuestActive => questActive;
    public bool IsQuestCompleted => questCompleted;
    public bool IsNarrativeRequestInProgress => narrativeRequestInProgress;
    public bool IsGenerating => narrativeRequestInProgress;
    public bool IsNarrativeGenerationFailed => narrativeGenerationFailed;
    public string CurrentNarrativeRequestId => currentNarrativeRequestId;

    // shows the scenario button for retry manual use or disabled automation
    public bool ShouldShowScenarioButton =>
        narrativeGenerationFailed ||
        showManualControlsInDevelopment ||
        !automaticallyRunScenarioLoop;
    public string PreviousStorySummary => previousStorySummary;

    // clears the shared instance when unity starts a new play session
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    private static void ResetStaticState()
    {
        Instance = null;
    }

    // sets the shared instance dependencies and saved story history
    private void Awake()
    {
        // removes a duplicate and keeps the existing quest system
        if (Instance != null && Instance != this)
        {
            Debug.Log(
                "Removing duplicate QuestSystem; the persistent quest state " +
                "will continue to be used.",
                this);
            enabled = false;
            Destroy(gameObject);
            return;
        }

        Instance = this;

        // finds a target resetter on this gameobject when none was assigned
        if (targetResetter == null)
        {
            targetResetter = GetComponent<ScenarioTargetResetter>();
        }

        // loads saved story history when saving between sessions is enabled
        if (persistNarrativeHistory)
        {
            previousStorySummary = PlayerPrefs.GetString(
                StoryHistoryPlayerPrefsKey,
                string.Empty);
        }
    }

    // updates controls and may start the automatic scenario loop
    private void Start()
    {
        UpdateStartButtonState();

        // starts only when no quest or story request is already active
        if (automaticallyRunScenarioLoop &&
            !questActive &&
            !narrativeRequestInProgress)
        {
            GenerateAndStartNextScenario();
        }
    }

    // creates one backend request from the scenario recap and tone
    public NarrativeGenerationRequest CreateNarrativeRequest(
        string previousStorySummary = "",
        string tone = NarrativeGenerationRequest.DefaultNarrativeTone)
    {
        // stops when there is no scenario to copy
        if (activeScenario == null)
        {
            Debug.LogError(
                "Cannot create a narrative request because no scenario is assigned.",
                this);
            return null;
        }

        // lets the request type copy fields and clean the tone
        return NarrativeGenerationRequest.FromScenario(
            activeScenario,
            previousStorySummary,
        tone);
    }

    // cleans the inspector tone and reports text that is too long
    private void OnValidate()
    {
        narrativeTone = NarrativeGenerationRequest.NormalizeTone(
            narrativeTone);

        // reports a long tone without changing the saved text
        if (narrativeTone.Length > MaximumBackendToneLength)
        {
            Debug.LogError(
                $"Narrative Tone exceeds the Backend limit of " +
                $"{MaximumBackendToneLength} characters.",
                this);
        }
    }

    // listens for enemy boss and item events while enabled
    private void OnEnable()
    {
        Enemy_Health.EnemyKilled += ReportEnemyKilled;
        Enemy_Health.BossKilled += ReportBossKilled;
        Inventory_Manager.ItemCollected += ReportItemCollected;
    }

    // stops listening while disabled
    private void OnDisable()
    {
        Enemy_Health.EnemyKilled -= ReportEnemyKilled;
        Enemy_Health.BossKilled -= ReportBossKilled;
        Inventory_Manager.ItemCollected -= ReportItemCollected;
    }

    // clears the shared instance when this manager is destroyed
    private void OnDestroy()
    {
        if (Instance == this)
        {
            Instance = null;
        }
    }

    // connects new scene ui objects to the saved quest state
    public void BindUI(
        TMP_Text newTitleText,
        TMP_Text newIntroductionText,
        TMP_Text newObjectiveText,
        TMP_Text newProgressText,
        TMP_Text newCompletionText,
        Button newStartButton,
        TMP_Text newStartButtonLabel)
    {
        titleText = newTitleText;
        introductionText = newIntroductionText;
        objectiveText = newObjectiveText;
        progressText = newProgressText;
        completionText = newCompletionText;
        startButton = newStartButton;
        startButtonLabel = newStartButtonLabel;

        // ends old loading state and redraws current quest content
        SetNarrativeRequestInProgress(false);
        RefreshUI();
    }

    // starts a new story request or retries the failed scenario
    public void StartScenario()
    {
        // reuses the failed scenario for retry
        if (narrativeGenerationFailed)
        {
            BeginNarrativeGeneration(true);
            return;
        }

        GenerateAndStartNextScenario();
    }

    // selects a fresh scenario and starts its story request
    public void GenerateAndStartNextScenario()
    {
        BeginNarrativeGeneration(false);
    }

    // selects a scenario and starts its complete story request flow
    private void BeginNarrativeGeneration(bool reuseSelectedScenario)
    {
        // blocks a second story request while one is running
        if (narrativeRequestInProgress)
        {
            Debug.LogWarning(
                "A narrative request is already in progress.",
                this);
            return;
        }

        // keeps the current quest until the player finishes it
        if (questActive && !questCompleted)
        {
            Debug.LogWarning(
                "Complete the active scenario before generating the next one.",
                this);
            return;
        }

        // reuses a failed choice only when retry is valid
        bool canReuseScenario =
            reuseSelectedScenario &&
            retrySelectedScenario &&
            activeScenario != null;

        // shows a retryable error when no valid scenario can be chosen
        if (!canReuseScenario && !SelectScenarioForNewRun())
        {
            retrySelectedScenario = false;
            EnterNarrativeGenerationFailure(
                string.Empty,
                "No valid scenario could be selected.");
            return;
        }

        // adds the current story recap and writing tone to the request
        NarrativeGenerationRequest requestData =
            CreateNarrativeRequest(previousStorySummary, narrativeTone);

        // stops before networking when the request cannot be created
        if (requestData == null)
        {
            retrySelectedScenario = false;
            EnterNarrativeGenerationFailure(
                string.Empty,
                "The narrative request could not be created.");
            return;
        }

        // keeps written map facts or adds a known scene description
        requestData.mapDescription = GetTargetSceneMapDescription(
            activeScenario,
            requestData.mapDescription);

        // marks this request as current before the backend call begins
        currentNarrativeRequestId = requestData.requestId;
        retrySelectedScenario = true;
        narrativeGenerationFailed = false;
        lastNarrativeGenerationError = string.Empty;
        Debug.Log(
            $"[NarrativeRequest {GetCurrentRequestId()}] Continuity " +
            (string.IsNullOrWhiteSpace(previousStorySummary)
                ? "context is empty (first completed story)."
                : $"context: {previousStorySummary}"),
            this);

        // shows loading state before contacting the backend
        SetNarrativeRequestInProgress(true);
        ShowLoadingUI();

        // uses local story text when no api client is assigned
        if (narrativeApiClient == null)
        {
            UseFallbackNarrative(
                currentNarrativeRequestId,
                "NarrativeApiClient is not assigned.");
            return;
        }

        // validates backend text and sends request errors to local fallback
        StartCoroutine(narrativeApiClient.GenerateNarrative(
            requestData,
            narrative => HandleBackendNarrative(
                requestData.requestId,
                narrative),
            reason => UseFallbackNarrative(
                requestData.requestId,
                reason)));
    }

    // selects one scenario from the inspector or shuffled cycle
    private bool SelectScenarioForNewRun()
    {
        // uses the inspector scenario when random selection is off
        if (!randomizeScenarioOnStart)
        {
            scenarioBag.Clear();

            // stops manual mode when no scenario was assigned
            if (activeScenario == null)
            {
                Debug.LogError(
                    "Cannot start a scenario because no ScenarioDefinition " +
                    "is assigned.",
                    this);
                return false;
            }

            lastSelectedScenarioId = activeScenario.scenarioId;
            return true;
        }

        // collects unique choices that have the needed quest data
        List<ScenarioDefinition> candidates =
            new List<ScenarioDefinition>();

        if (availableScenarios != null)
        {
            // skips missing invalid or repeated scenario ids
            foreach (ScenarioDefinition scenario in availableScenarios)
            {
                if (scenario != null &&
                    !string.IsNullOrWhiteSpace(scenario.scenarioId) &&
                    !string.IsNullOrWhiteSpace(scenario.targetId) &&
                    scenario.requiredAmount > 0 &&
                    !candidates.Exists(
                        candidate =>
                            candidate.scenarioId == scenario.scenarioId))
                {
                    candidates.Add(scenario);
                }
            }
        }

        // stops when random mode has no valid choices
        if (candidates.Count == 0)
        {
            Debug.LogError(
                "Random scenario selection requires at least one valid " +
                "Available Scenario.",
                this);
            return false;
        }

        // removes cycle entries that are no longer in the inspector list
        scenarioBag.RemoveAll(
            bagScenario =>
                bagScenario == null ||
                !candidates.Exists(
                    candidate =>
                            candidate.scenarioId == bagScenario.scenarioId));

        // refills the cycle after every choice was used
        if (scenarioBag.Count == 0)
        {
            RefillScenarioBag(candidates);
        }

        // takes the first shuffled choice and remembers it
        activeScenario = scenarioBag[0];
        scenarioBag.RemoveAt(0);
        lastSelectedScenarioId = activeScenario.scenarioId;

        Debug.Log(
            $"Randomly selected scenario '{activeScenario.scenarioId}' " +
            $"({activeScenario.scenarioType}, target " +
            $"'{activeScenario.targetId}', amount " +
            $"{activeScenario.requiredAmount}). Fair cycle remaining: " +
            $"{scenarioBag.Count}.",
            this);
        return true;
    }

    // returns written map facts or a known scene description
    private static string GetTargetSceneMapDescription(
        ScenarioDefinition scenario,
        string fallback)
    {
        // keeps written map facts when they contain text
        if (!string.IsNullOrWhiteSpace(fallback))
        {
            return fallback;
        }

        // changes known scene names into useful story context
        switch (scenario?.targetSceneName)
        {
            case "Forest":
                return "A ruined forest settlement crossed by an old road, " +
                       "with a black castle to the north, scattered houses, " +
                       "ancient trees, rocky rises, and a dark western cave.";

            case "Arena":
                return "An abandoned grassy arena enclosed by mountain " +
                       "ridges, old paths, ruined structures, and sparse " +
                       "trees beneath an open sky.";

            default:
                return string.IsNullOrWhiteSpace(fallback)
                    ? "Weathered ruins beneath an open sky, with wild " +
                      "grass and young trees growing among the old stones."
                    : fallback;
        }
    }

    // creates a shuffled cycle and avoids a repeat between cycles
    private void RefillScenarioBag(
        List<ScenarioDefinition> candidates)
    {
        // adds every valid choice once to the new cycle
        scenarioBag.Clear();
        scenarioBag.AddRange(candidates);

        // shuffles all choices into a random order
        for (int index = scenarioBag.Count - 1; index > 0; index--)
        {
            int swapIndex = Random.Range(0, index + 1);
            ScenarioDefinition temporaryScenario = scenarioBag[index];
            scenarioBag[index] = scenarioBag[swapIndex];
            scenarioBag[swapIndex] = temporaryScenario;
        }

        // swaps the first choice when it repeats the last cycle choice
        if (avoidImmediateRepeat &&
            scenarioBag.Count > 1 &&
            !string.IsNullOrWhiteSpace(lastSelectedScenarioId) &&
            scenarioBag[0].scenarioId == lastSelectedScenarioId)
        {
            int swapIndex = Random.Range(1, scenarioBag.Count);
            ScenarioDefinition temporaryScenario = scenarioBag[0];
            scenarioBag[0] = scenarioBag[swapIndex];
            scenarioBag[swapIndex] = temporaryScenario;
        }

        // logs how many choices are ready in this cycle
        Debug.Log(
            $"Refilled fair scenario cycle with " +
            $"{scenarioBag.Count} unique scenario(s).",
            this);
    }

    // validates backend story text and starts the current scenario
    private void HandleBackendNarrative(
        string requestId,
        GeneratedNarrative narrative)
    {
        // ignores an old or repeated response
        if (!IsCurrentNarrativeRequest(requestId))
        {
            LogIgnoredStaleNarrativeResponse(requestId, "backend success");
            return;
        }

        // uses local fallback when unity rejects backend story text
        if (!NarrativeValidator.TryValidate(
                narrative,
                activeScenario,
                out string validationError))
        {
            UseFallbackNarrative(
                requestId,
                $"Backend narrative failed Unity validation: " +
                validationError);
            return;
        }

        // shows a generation error when scenario targets cannot be prepared
        if (!BeginScenarioWithNarrative(
                narrative,
                "backend",
                true,
                string.Empty,
                string.Empty))
        {
            EnterNarrativeGenerationFailure(
                requestId,
                "The generated scenario targets could not be prepared.");
        }
    }

    // creates checks and starts local story text after backend failure
    private void UseFallbackNarrative(string requestId, string reason)
    {
        // ignores a failure from an old or completed request
        if (!IsCurrentNarrativeRequest(requestId))
        {
            LogIgnoredStaleNarrativeResponse(requestId, "backend failure");
            return;
        }

        Debug.LogWarning(
            $"[NarrativeRequest {GetCurrentRequestId()}] " +
            $"Narrative backend unavailable. Using local fallback. {reason}",
            this);

        // stops when no local story provider is assigned
        if (narrativeProvider == null)
        {
            EnterNarrativeGenerationFailure(
                requestId,
                reason +
                " Local fallback is unavailable because no " +
                "NarrativeTestProvider is assigned.");
            return;
        }

        // turns local provider errors into a safe retry state
        GeneratedNarrative fallbackNarrative;
        try
        {
            fallbackNarrative =
                narrativeProvider.GenerateTestNarrative(activeScenario);
        }
        catch (System.Exception error)
        {
            EnterNarrativeGenerationFailure(
                requestId,
                reason + " Local fallback threw an exception: " +
                error.Message);
            return;
        }

        // checks local story text with the same rules as backend text
        if (!NarrativeValidator.TryValidate(
                fallbackNarrative,
                activeScenario,
                out string validationError))
        {
            EnterNarrativeGenerationFailure(
                requestId,
                reason +
                " Local fallback failed validation: " +
                validationError);
            return;
        }

        // keeps unity validation errors separate from request errors
        string unityValidationError = reason.StartsWith(
            "Backend narrative failed Unity validation:",
            System.StringComparison.Ordinal)
                ? reason
                : string.Empty;

        // starts local story text and records why it was needed
        if (!BeginScenarioWithNarrative(
                fallbackNarrative,
                "local_fallback",
                false,
                unityValidationError,
                reason))
        {
            EnterNarrativeGenerationFailure(
                requestId,
                reason +
                " Local fallback was created, but the scenario targets " +
                "could not be prepared.");
        }
    }

    // prepares targets and turns accepted story text into an active scenario
    private bool BeginScenarioWithNarrative(
        GeneratedNarrative narrative,
        string source,
        bool backendNarrativeAccepted,
        string unityValidationError,
        string fallbackReason)
    {
        // stops when the target resetter cannot prepare gameplay targets
        if (targetResetter != null &&
            !targetResetter.ResetTargetsForScenario(activeScenario))
        {
            Debug.LogError(
                $"Scenario '{activeScenario.scenarioId}' could not start " +
                "because its fixed gameplay targets could not be reset.",
                this);
            return false;
        }

        // allows older setups to continue when no resetter is assigned
        if (targetResetter == null)
        {
            Debug.LogWarning(
                "ScenarioTargetResetter is not assigned; consecutive " +
                "scenarios may run out of gameplay targets.",
                this);
        }

        // resets quest state and starts gameplay time after preparation checks
        activeNarrative = narrative;
        currentProgress = 0;
        questActive = true;
        questCompleted = false;
        activeScenarioStartedAt = Time.realtimeSinceStartup;

        // stores story source and fallback details for gameplay logs
        activeNarrativeSource = source;
        backendNarrativeAcceptedByUnity = backendNarrativeAccepted;
        activeUnityValidationError = TruncateExperimentText(
            unityValidationError);
        activeFallbackReason = TruncateExperimentText(fallbackReason);
        retrySelectedScenario = false;
        narrativeGenerationFailed = false;
        lastNarrativeGenerationError = string.Empty;

        // refreshes ui ends loading and records the scenario start
        RefreshUI();
        SetNarrativeRequestInProgress(false);
        RecordScenarioRunEvent(
            "scenario_started",
            false,
            0f);
        Debug.Log(
            $"[NarrativeRequest {GetCurrentRequestId()}] " +
            $"Started scenario '{activeScenario.scenarioId}' " +
            $"using narrative from {source}.",
            this);
        return true;
    }

    // adds one matching enemy kill to an active combat scenario
    public void ReportEnemyKilled(string enemyId)
    {
        // ignores kills when no unfinished quest is active
        if (!questActive || questCompleted)
        {
            return;
        }

        // ignores enemy events for other scenario types
        if (activeScenario == null ||
            activeScenario.scenarioType != ScenarioType.KillEnemies)
        {
            return;
        }

        // accepts only the target id set by the scenario
        if (enemyId != activeScenario.targetId)
        {
            return;
        }

        // adds one without going above the required amount
        currentProgress = Mathf.Min(
            currentProgress + 1,
            activeScenario.requiredAmount);

        RefreshUI();

        // completes the scenario when progress reaches the requirement
        if (currentProgress >= activeScenario.requiredAmount)
        {
            CompleteScenario();
        }
    }

    // adds matching items to an active collection scenario
    public void ReportItemCollected(string itemId, int amount)
    {
        // ignores the wrong target or an amount below one
        if (!CanProgressScenario(ScenarioType.CollectItems, itemId) ||
            amount <= 0)
        {
            return;
        }

        AddProgress(amount);
    }

    // adds one matching boss death to an active boss scenario
    public void ReportBossKilled(string bossId)
    {
        if (!CanProgressScenario(ScenarioType.SlayBoss, bossId))
        {
            return;
        }

        AddProgress(1);
    }

    // checks active state scenario type and target id
    private bool CanProgressScenario(
        ScenarioType expectedType,
        string reportedTargetId)
    {
        return questActive &&
               !questCompleted &&
               activeScenario != null &&
               activeScenario.scenarioType == expectedType &&
               reportedTargetId == activeScenario.targetId;
    }

    // adds progress updates ui and completes at the required amount
    private void AddProgress(int amount)
    {
        // keeps progress from going above the required amount
        currentProgress = Mathf.Min(
            currentProgress + amount,
            activeScenario.requiredAmount);

        RefreshUI();

        // completes after progress reaches the requirement
        if (currentProgress >= activeScenario.requiredAmount)
        {
            CompleteScenario();
        }
    }

    // finishes one scenario saves its recap and starts the next step
    private void CompleteScenario()
    {
        // prevents repeated completion logs or rewards
        if (!questActive || questCompleted)
        {
            return;
        }

        questActive = false;
        questCompleted = true;

        // saves the story recap before the next automatic request
        SaveCompletedStorySummary();
        UpdateStartButtonState();

        // shows completion text when the label exists
        if (completionText != null)
        {
            completionText.text = activeNarrative?.completionText ?? string.Empty;
        }

        // gives the fixed experience reward when the manager exists
        if (ExpManager.Instance != null &&
            activeScenario.experienceReward > 0)
        {
            ExpManager.Instance.GainExperience(
                activeScenario.experienceReward);
        }

        // gold reward is saved in the scenario but is not connected yet

        // logs completed rewards including the unconnected gold value
        Debug.Log(
            $"Completed scenario '{activeScenario.scenarioId}'. " +
            $"Rewarded {activeScenario.experienceReward} EXP. " +
            $"{activeScenario.goldReward} gold is pending inventory integration.",
            this);

        // records gameplay time without story generation wait time
        float completionTimeSeconds = Mathf.Max(
            0f,
            Time.realtimeSinceStartup - activeScenarioStartedAt);
        RecordScenarioRunEvent(
            "scenario_completed",
            true,
            completionTimeSeconds);

        // tells listeners after all completion state is ready
        QuestStateChanged?.Invoke();

        // starts the next random choice when automatic mode is on
        if (automaticallyRunScenarioLoop)
        {
            GenerateAndStartNextScenario();
        }
    }

    // builds and sends one scenario start or completion log
    private void RecordScenarioRunEvent(
        string eventType,
        bool completed,
        float elapsedSeconds)
    {
        // skips optional logging when needed data is missing
        if (narrativeApiClient == null || activeScenario == null)
        {
            return;
        }

        // copies current gameplay story source and fallback details
        ScenarioRunEvent runEvent = new ScenarioRunEvent
        {
            requestId = GetCurrentRequestId(),
            scenarioId = activeScenario.scenarioId,
            scenarioType = activeScenario.scenarioType.ToString(),
            eventType = eventType,
            completed = completed,
            elapsedSeconds = Mathf.Max(0f, elapsedSeconds),
            currentProgress = currentProgress,
            requiredAmount = activeScenario.requiredAmount,
            narrativeSource = activeNarrativeSource,
            backendNarrativeAcceptedByUnity =
                backendNarrativeAcceptedByUnity,
            unityValidationError = activeUnityValidationError,
            fallbackReason = activeFallbackReason
        };

        // sends the log without blocking or changing gameplay success
        StartCoroutine(narrativeApiClient.RecordRunEvent(runEvent));
    }

    // cleans and limits error text for a backend event
    private static string TruncateExperimentText(string value)
    {
        const int maximumLength = 1000;
        string normalizedValue = value?.Trim() ?? string.Empty;
        return normalizedValue.Length <= maximumLength
            ? normalizedValue
            : normalizedValue.Substring(0, maximumLength);
    }

    // redraws story objective and progress from current quest state
    private void RefreshUI()
    {
        // waits until both story text and scenario data exist
        if (activeNarrative == null || activeScenario == null)
        {
            return;
        }

        // updates each label only when it is available
        if (titleText != null)
        {
            titleText.text = activeNarrative.title;
        }

        if (introductionText != null)
        {
            introductionText.text = activeNarrative.introduction;
        }

        // builds the objective from fixed scenario rules
        if (objectiveText != null)
        {
            objectiveText.text = BuildObjectiveText();
        }

        // shows current progress beside the required amount
        if (progressText != null)
        {
            progressText.text =
                $"{currentProgress} / {activeScenario.requiredAmount}";
        }

        // clears old completion text during an unfinished scenario
        if (completionText != null && !questCompleted)
        {
            completionText.text = string.Empty;
        }
    }

    // shows loading text for the first or next story request
    private void ShowLoadingUI()
    {
        // checks whether this request prepares a later scenario
        bool preparingNextScenario = questCompleted;

        // fills available labels with loading text
        if (titleText != null)
        {
            titleText.text = preparingNextScenario
                ? "Preparing next scenario..."
                : "Generating narrative...";
        }

        if (introductionText != null)
        {
            introductionText.text = preparingNextScenario
                ? "Generating the next narrative in the background."
                : "Contacting the local narrative backend.";
        }

        if (objectiveText != null)
        {
            objectiveText.text = preparingNextScenario
                ? "Next objective: —"
                : "Objective: —";
        }

        if (progressText != null)
        {
            progressText.text = "—";
        }
    }

    // enters a safe retry state when no story path can start gameplay
    private void EnterNarrativeGenerationFailure(
        string requestId,
        string reason)
    {
        // ignores a delayed failure from an older request
        if (!string.IsNullOrWhiteSpace(requestId) &&
            !IsCurrentNarrativeRequest(requestId))
        {
            LogIgnoredStaleNarrativeResponse(requestId, "failure state");
            return;
        }

        // stops generation and stores a short reason for retry logs
        narrativeRequestInProgress = false;
        narrativeGenerationFailed = true;
        questActive = false;
        lastNarrativeGenerationError = TruncateExperimentText(reason);

        // replaces quest text with a clear retry message
        if (titleText != null)
        {
            titleText.text = "Narrative generation failed";
        }

        if (introductionText != null)
        {
            introductionText.text =
                "The next scenario could not be prepared automatically. " +
                "You can retry safely.";
        }

        if (objectiveText != null)
        {
            objectiveText.text = "Press Retry to try this scenario again.";
        }

        if (progressText != null)
        {
            progressText.text = "—";
        }

        // updates the button and listeners after failure state is ready
        UpdateStartButtonState();
        QuestStateChanged?.Invoke();

        // logs the final error with its request id
        Debug.LogError(
            $"[NarrativeRequest {GetCurrentRequestId()}] " +
            $"Narrative generation stopped. {lastNarrativeGenerationError}",
            this);
    }

    // accepts callbacks only for the request still in progress
    private bool IsCurrentNarrativeRequest(string requestId)
    {
        return narrativeRequestInProgress &&
               !string.IsNullOrWhiteSpace(requestId) &&
               requestId == currentNarrativeRequestId;
    }

    // logs an ignored old or repeated callback
    private void LogIgnoredStaleNarrativeResponse(
        string requestId,
        string responseType)
    {
        Debug.LogWarning(
            $"[NarrativeRequest {requestId}] Ignored stale " +
            $"{responseType}; current request is " +
            $"'{GetCurrentRequestId()}'.",
            this);
    }

    // builds player instructions from fixed rules and checked display names
    private string BuildObjectiveText()
    {
        // chooses one target name or many target names from the amount
        string singularName = activeNarrative.targetDisplayNameSingular.Trim();
        string pluralName = activeNarrative.targetDisplayNamePlural.Trim();
        int requiredAmount = activeScenario.requiredAmount;
        string targetName = requiredAmount == 1
            ? singularName
            : pluralName;

        // adds a destination when targets belong to one scene
        string destination = string.IsNullOrWhiteSpace(
            activeScenario.targetSceneName)
                ? string.Empty
                : $"{activeScenario.targetSceneName}: ";

        // chooses collect or defeat from the fixed scenario type
        switch (activeScenario.scenarioType)
        {
            case ScenarioType.CollectItems:
                return $"{destination}Collect {requiredAmount} {targetName}.";

            case ScenarioType.SlayBoss:
            case ScenarioType.KillEnemies:
            default:
                return $"{destination}Defeat {requiredAmount} {targetName}.";
        }
    }

    // updates story request state button behavior and listeners
    private void SetNarrativeRequestInProgress(bool isInProgress)
    {
        narrativeRequestInProgress = isInProgress;

        UpdateStartButtonState();
        QuestStateChanged?.Invoke();
    }

    // controls the scenario button from current quest state
    private void UpdateStartButtonState()
    {
        // blocks another scenario while current gameplay is unfinished
        bool hasActiveUnfinishedScenario = questActive && !questCompleted;

        // enables the button only when starting or retrying is safe
        if (startButton != null)
        {
            startButton.interactable =
                ShouldShowScenarioButton &&
                !narrativeRequestInProgress &&
                !hasActiveUnfinishedScenario;
        }

        // chooses a label for failure loading active completed or idle state
        if (startButtonLabel != null)
        {
            if (narrativeGenerationFailed)
            {
                startButtonLabel.text = "RETRY";
            }
            else if (narrativeRequestInProgress)
            {
                startButtonLabel.text = "GENERATING...";
            }
            else if (hasActiveUnfinishedScenario)
            {
                startButtonLabel.text = "SCENARIO ACTIVE";
            }
            else if (questCompleted)
            {
                startButtonLabel.text = "NEXT SCENARIO";
            }
            else
            {
                startButtonLabel.text = "START SCENARIO";
            }
        }
    }

    // updates the story recap and may save it between play sessions
    private void SaveCompletedStorySummary()
    {
        // keeps the last recap when the new one is empty
        string completedSummary = activeNarrative?.storySummary?.Trim();
        if (string.IsNullOrWhiteSpace(completedSummary))
        {
            Debug.LogWarning(
                "The completed narrative has no storySummary; " +
                "continuity history was not updated.",
                this);
            return;
        }

        // updates story history in memory for the next request
        previousStorySummary = completedSummary;

        // writes story history to playerprefs when saving is enabled
        if (persistNarrativeHistory)
        {
            PlayerPrefs.SetString(
                StoryHistoryPlayerPrefsKey,
                previousStorySummary);
            PlayerPrefs.Save();
        }

        // logs the exact story recap saved in memory
        Debug.Log(
            $"Saved narrative continuity summary: {previousStorySummary}",
        this);
    }

    // clears current and older story history from the inspector menu
    [ContextMenu("Clear Narrative History")]
    public void ClearNarrativeHistory()
    {
        previousStorySummary = string.Empty;
        PlayerPrefs.DeleteKey(StoryHistoryPlayerPrefsKey);
        PlayerPrefs.DeleteKey(LegacyStoryHistoryPlayerPrefsKey);
        PlayerPrefs.Save();
        Debug.Log("Cleared narrative continuity history.", this);
    }

    // returns clear text when no request id exists yet
    private string GetCurrentRequestId()
    {
        return string.IsNullOrWhiteSpace(currentNarrativeRequestId)
            ? "not-created"
            : currentNarrativeRequestId;
    }
}
