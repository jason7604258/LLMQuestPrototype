using TMPro;
using System;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

// stores player experience, handles level gains, and refreshes the level display
[DefaultExecutionOrder(-90)]
[DisallowMultipleComponent]
public class ExpManager : MonoBehaviour
{
    // exposes the active experience manager without allowing outside replacement
    public static ExpManager Instance { get; private set; }

    // stores the current level and the growing experience requirement
    [Header("Level Progression")]
    [Min(1)] public int level = 1;
    [Min(0)] public int currentExp;
    [Min(1)] public int expToLevel = 10;
    [Min(1f)] public float expGrowthMultiplier = 1.2f;

    // points to the experience bar and level label in the persistent ui
    [Header("UI")]
    [SerializeField] private Slider expSlider;
    [SerializeField] private TMP_Text currentLevelText;

    // tells other systems when the player reaches a new level
    public event Action<int> LevelGained;

    // keeps one manager and makes inspector values safe before use
    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            // the existing manager already owns the player progression
            Debug.LogWarning("Duplicate ExpManager disabled. Keep only one in the scene.", this);
            Destroy(this);
            return;
        }

        Instance = this;
        level = Mathf.Max(1, level);
        currentExp = Mathf.Max(0, currentExp);
        expToLevel = Mathf.Max(1, expToLevel);
        expGrowthMultiplier = Mathf.Max(1f, expGrowthMultiplier);
    }

    // applies any experience already above the limit and draws the first ui state
    private void Start()
    {
        while (currentExp >= expToLevel)
        {
            LevelUp();
        }

        UpdateUI();
    }

    // watches for scene ui changes while this object owns the singleton
    private void OnEnable()
    {
        if (Instance != this)
        {
            return;
        }

        SceneManager.sceneLoaded -= HandleSceneLoaded;
        SceneManager.sceneLoaded += HandleSceneLoaded;
    }

    // removes the scene callback before this component stops running
    private void OnDisable()
    {
        if (Instance == this)
        {
            SceneManager.sceneLoaded -= HandleSceneLoaded;
        }
    }

    // reconnects ui references and redraws them after a scene change
    private void HandleSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        RebindSceneUI(scene);
        UpdateUI();
    }

    // finds the experience ui from persistent objects or the loaded scene
    private void RebindSceneUI(Scene scene)
    {
        GameObject expCanvas = GameManager.Instance != null
            ? GameManager.Instance.FindPersistentObject("ExpCanvas")
            : null;

        if (expCanvas == null)
        {
            // this fallback also supports scenes running without the game manager
            foreach (GameObject root in scene.GetRootGameObjects())
            {
                if (root.name == "ExpCanvas")
                {
                    expCanvas = root;
                    break;
                }
            }
        }

        if (expCanvas == null)
        {
            return;
        }

        expSlider = expCanvas.GetComponentInChildren<Slider>(true);
        currentLevelText = null;

        TMP_Text[] labels = expCanvas.GetComponentsInChildren<TMP_Text>(true);
        foreach (TMP_Text label in labels)
        {
            // the level label is selected by its authored object name
            if (label != null && label.gameObject.name == "Text (TMP)")
            {
                currentLevelText = label;
                break;
            }
        }
    }

    // adds positive experience and allows several level gains at once
    public void GainExperience(int amount)
    {
        if (amount <= 0)
        {
            return;
        }

        currentExp += amount;

        while (currentExp >= expToLevel)
        {
            LevelUp();
        }

        UpdateUI();
    }

    // spends the current level cost and grows the cost for the next level
    private void LevelUp()
    {
        currentExp -= expToLevel;
        level++;
        expToLevel = Mathf.Max(
            expToLevel + 1,
            Mathf.RoundToInt(expToLevel * expGrowthMultiplier));
        LevelGained?.Invoke(level);
    }

    // copies the current progression values into the visible ui controls
    public void UpdateUI()
    {
        if (expSlider != null)
        {
            expSlider.minValue = 0f;
            expSlider.maxValue = expToLevel;
            expSlider.value = currentExp;
        }

        if (currentLevelText != null)
        {
            currentLevelText.text = $"Level: {level}";
        }
    }

    // clears singleton ownership only when the active manager is destroyed
    private void OnDestroy()
    {
        if (Instance == this)
        {
            SceneManager.sceneLoaded -= HandleSceneLoaded;
            Instance = null;
        }
    }
}
