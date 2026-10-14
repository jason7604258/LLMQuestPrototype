using System;
using UnityEngine;
using TMPro;

[DisallowMultipleComponent]
// manages skill points unlock rules purchases and panel visibility
public class SkillTreeManager : MonoBehaviour
{
    // skill slots point display and point reward for each player level
    public SkillSlot[] skillSlots;
    public TMP_Text pointsText;
    [Min(0)] public int pointsPerLevel = 1;
    public int availablePoints;

    // panel link and keyboard settings
    [Header("Panel")]
    [SerializeField] private CanvasGroup skillTreeCanvas;
    [SerializeField] private KeyCode toggleKey = KeyCode.K;
    [SerializeField] private bool startsOpen;

    // level system that awards new skill points
    [Header("Progression")]
    [SerializeField] private ExpManager experienceManager;

    // lets other systems react after a successful purchase
    public event Action<SkillSlot> SkillPurchased;

    // setup and visibility state
    private bool initialized;
    private bool isOpen;

    // fixes starting values and prepares panel slots and level events
    private void Awake()
    {
        availablePoints = Mathf.Max(0, availablePoints);
        pointsPerLevel = Mathf.Max(0, pointsPerLevel);
        InitializePanel();
        DiscoverSlotsIfNeeded();
        AttachExperienceManager();
    }

    // binds slot buttons unlocks valid roots and shows the starting panel state
    private void Start()
    {
        BindSlots();
        RefreshUnlocks();
        RefreshAllUI();
        SetPanelOpen(startsOpen);
        initialized = true;
    }

    // reconnects runtime listeners after this tree is enabled again
    private void OnEnable()
    {
        if (initialized)
        {
            BindSlots();
            AttachExperienceManager();
            RefreshAllUI();
        }
    }

    // removes listeners while the skill tree is inactive
    private void OnDisable()
    {
        UnbindSlots();
        DetachExperienceManager();
    }

    // toggles the skill tree when the configured key is pressed
    private void Update()
    {
        if (Input.GetKeyDown(toggleKey))
        {
            SetPanelOpen(!isOpen);
        }
    }

    // validates and applies one skill purchase as a single action
    public bool TryPurchaseSkill(SkillSlot slot)
    {
        if (!OwnsSlot(slot) || !slot.CanPurchase(availablePoints))
        {
            return false;
        }

        if (!slot.TryCommitUpgrade(StatsManager.Instance))
        {
            return false;
        }

        // spend points only after the stat change succeeds
        availablePoints -= slot.PointCost;
        RefreshUnlocks();
        RefreshAllUI();
        SkillPurchased?.Invoke(slot);
        return true;
    }

    // changes available points without allowing a negative balance
    public void UpdateAbilityPoints(int amount)
    {
        availablePoints = Mathf.Max(0, availablePoints + amount);
        RefreshAllUI();
    }

    // shows or hides the panel without disabling the manager
    public void SetPanelOpen(bool shouldOpen)
    {
        isOpen = shouldOpen;
        if (skillTreeCanvas == null)
        {
            return;
        }

        skillTreeCanvas.alpha = isOpen ? 1f : 0f;
        skillTreeCanvas.interactable = isOpen;
        skillTreeCanvas.blocksRaycasts = isOpen;

        if (isOpen)
        {
            RefreshAllUI();
        }
    }

    // finds or creates the canvas group used for panel visibility
    private void InitializePanel()
    {
        if (skillTreeCanvas == null)
        {
            skillTreeCanvas = GetComponent<CanvasGroup>();
        }

        if (skillTreeCanvas == null)
        {
            // a canvas group is needed to hide visuals and block input together
            skillTreeCanvas = gameObject.AddComponent<CanvasGroup>();
        }

        RectTransform rect = transform as RectTransform;
        if (rect != null && rect.localScale.sqrMagnitude < 0.001f)
        {
            rect.localScale = Vector3.one;
        }
    }

    // finds child skill slots when none were assigned
    private void DiscoverSlotsIfNeeded()
    {
        if (skillSlots == null || skillSlots.Length == 0)
        {
            skillSlots = GetComponentsInChildren<SkillSlot>(true);
        }
    }

    // connects every valid slot button to this manager
    private void BindSlots()
    {
        DiscoverSlotsIfNeeded();
        if (skillSlots == null)
        {
            return;
        }

        foreach (SkillSlot slot in skillSlots)
        {
            slot?.Bind(this);
        }
    }

    // removes this manager from every slot button
    private void UnbindSlots()
    {
        if (skillSlots == null)
        {
            return;
        }

        foreach (SkillSlot slot in skillSlots)
        {
            slot?.Unbind(this);
        }
    }

    // prevents purchases from slots outside this skill tree
    private bool OwnsSlot(SkillSlot target)
    {
        if (target == null || skillSlots == null)
        {
            return false;
        }

        foreach (SkillSlot slot in skillSlots)
        {
            if (slot == target)
            {
                return true;
            }
        }

        return false;
    }

    // unlocks every skill whose prerequisites are now complete
    private void RefreshUnlocks()
    {
        if (skillSlots == null)
        {
            return;
        }

        bool changed;
        // repeat because one new unlock may allow another skill to unlock
        do
        {
            changed = false;
            foreach (SkillSlot slot in skillSlots)
            {
                if (slot != null && slot.IsConfigured && !slot.isUnlocked &&
                    slot.CanUnlockSkill())
                {
                    slot.Unlock();
                    changed = true;
                }
            }
        }
        while (changed);
    }

    // redraws the point count and every skill slot
    private void RefreshAllUI()
    {
        if (pointsText != null)
        {
            pointsText.text = $"Points: {availablePoints}";
        }

        if (skillSlots == null)
        {
            return;
        }

        foreach (SkillSlot slot in skillSlots)
        {
            slot?.RefreshUI(availablePoints);
        }
    }

    // finds the level manager and listens for future levels
    private void AttachExperienceManager()
    {
        if (experienceManager == null)
        {
            experienceManager = ExpManager.Instance;
        }

        if (experienceManager != null)
        {
            experienceManager.LevelGained -= HandleLevelGained;
            experienceManager.LevelGained += HandleLevelGained;
        }
    }

    // stops listening to the current level manager
    private void DetachExperienceManager()
    {
        if (experienceManager != null)
        {
            experienceManager.LevelGained -= HandleLevelGained;
        }
    }

    // awards the configured points for each gained level
    private void HandleLevelGained(int newLevel)
    {
        UpdateAbilityPoints(pointsPerLevel);
    }
}
