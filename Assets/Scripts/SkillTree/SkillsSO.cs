using UnityEngine;

[CreateAssetMenu(fileName = "NewSkill", menuName = "SkillTree/Skill")]
// stores reusable skill data and the stat change for each level
public class SkillsSO : ScriptableObject
{
    // stat changes currently supported by the player stats system
    public enum EffectType
    {
        None,
        MaxHealth,
        Damage,
        MoveSpeed
    }

    // name level limit point cost and icon for this skill
    public string skillName;
    [Min(1)] public int maxLevel = 1;
    [Min(1)] public int pointCost = 1;
    public Sprite skillIcon;

    // stat change applied once for every purchased level
    [Header("Effect Per Level")]
    public EffectType effectType;
    [Min(0f)] public float effectAmount = 1f;

    // applies this skill effect when its type and stats manager are valid
    public bool TryApplyEffect(StatsManager statsManager)
    {
        if (effectType == EffectType.None)
        {
            // skills with no effect still allow their level to advance
            return true;
        }

        if (statsManager == null)
        {
            Debug.LogWarning($"Cannot apply skill '{name}': StatsManager is missing.");
            return false;
        }

        statsManager.ApplySkillUpgrade(effectType, effectAmount);
        return true;
    }

    // keeps inspector values inside their valid ranges
    private void OnValidate()
    {
        maxLevel = Mathf.Max(1, maxLevel);
        pointCost = Mathf.Max(1, pointCost);
        effectAmount = Mathf.Max(0f, effectAmount);
    }
}
