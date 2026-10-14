using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

[DisallowMultipleComponent]
// stores one skill state and forwards its button click to the skill tree
public class SkillSlot : MonoBehaviour
{
    // skill data and any skills that must be maxed first
    public List<SkillSlot> prerequisiteSkillSlots = new List<SkillSlot>();
    public SkillsSO skillSO;

    // saved progress for this skill
    public int currentLevel;
    public bool isUnlocked;

    // ui elements used to show and buy this skill
    public Image skillIcon;
    public Button skillButton;
    public TMP_Text skillLevelText;

    // skill tree that owns purchases from this slot
    private SkillTreeManager owner;

    // common checks used by the tree and ui
    public bool IsConfigured => skillSO != null && skillSO.maxLevel > 0;
    public bool IsMaxed => IsConfigured && currentLevel >= skillSO.maxLevel;
    public int PointCost => IsConfigured ? Mathf.Max(1, skillSO.pointCost) : int.MaxValue;

    // prepares ui links and fixes the starting state
    private void Awake()
    {
        CacheUIReferences();
        SanitizeState();
        RefreshUI(0);
    }

    // keeps editor values valid and refreshes the preview
    private void OnValidate()
    {
        CacheUIReferences();
        SanitizeState();
        RefreshUI(0);
    }

    // gives this slot an owner and connects its button
    internal void Bind(SkillTreeManager manager)
    {
        owner = manager;
        if (skillButton == null)
        {
            return;
        }

        skillButton.onClick.RemoveListener(HandleClick);
        skillButton.onClick.AddListener(HandleClick);
    }

    // removes the button listener added by the given owner
    internal void Unbind(SkillTreeManager manager)
    {
        if (skillButton != null)
        {
            skillButton.onClick.RemoveListener(HandleClick);
        }

        if (owner == manager)
        {
            owner = null;
        }
    }

    // sends purchase checks to the owning skill tree
    private void HandleClick()
    {
        owner?.TryPurchaseSkill(this);
    }

    // refreshes the icon level text and button availability
    public void RefreshUI(int availablePoints)
    {
        CacheUIReferences();

        if (skillIcon != null)
        {
            // keep the scene icon for placeholders and use skill data when configured
            if (skillSO != null && skillSO.skillIcon != null)
            {
                skillIcon.sprite = skillSO.skillIcon;
            }

            skillIcon.color = IsConfigured && isUnlocked ? Color.white : Color.grey;
        }

        if (skillLevelText != null)
        {
            if (!IsConfigured)
            {
                skillLevelText.text = "Invalid";
            }
            else if (!isUnlocked)
            {
                skillLevelText.text = "Locked";
            }
            else
            {
                skillLevelText.text = $"{currentLevel}/{skillSO.maxLevel}";
            }
        }

        if (skillButton != null)
        {
            skillButton.interactable = CanPurchase(availablePoints);
        }
    }

    // applies one valid upgrade before the tree spends any points
    internal bool TryCommitUpgrade(StatsManager statsManager)
    {
        if (!IsConfigured || !isUnlocked || IsMaxed ||
            !skillSO.TryApplyEffect(statsManager))
        {
            return false;
        }

        currentLevel++;
        return true;
    }

    // marks this skill as available for purchase
    internal void Unlock()
    {
        isUnlocked = true;
    }

    // checks configuration unlock state level and point cost
    public bool CanPurchase(int availablePoints)
    {
        return IsConfigured && isUnlocked && !IsMaxed &&
               availablePoints >= PointCost;
    }

    // requires every listed prerequisite to be valid unlocked and maxed
    public bool CanUnlockSkill()
    {
        if (prerequisiteSkillSlots == null || prerequisiteSkillSlots.Count == 0)
        {
            return true;
        }

        foreach (SkillSlot slot in prerequisiteSkillSlots)
        {
            if (slot == null || slot == this || !slot.IsConfigured ||
                !slot.isUnlocked || !slot.IsMaxed)
            {
                return false;
            }
        }

        return true;
    }

    // finds button and level text links when they are not assigned
    private void CacheUIReferences()
    {
        if (skillButton == null)
        {
            skillButton = GetComponent<Button>();
        }

        if (skillLevelText == null)
        {
            skillLevelText = GetComponentInChildren<TMP_Text>(true);
        }
    }

    // keeps the saved level inside this skill valid range
    private void SanitizeState()
    {
        currentLevel = Mathf.Max(0, currentLevel);
        if (skillSO != null)
        {
            currentLevel = Mathf.Min(currentLevel, Mathf.Max(1, skillSO.maxLevel));
        }
    }
}
