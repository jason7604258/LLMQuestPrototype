using UnityEngine;
using System;

// stores shared player combat, movement, and health values
[DefaultExecutionOrder(-100)]
[DisallowMultipleComponent]
public class StatsManager : MonoBehaviour
{
    // exposes the active stats manager without allowing outside replacement
    public static StatsManager Instance { get; private set; }

    // controls melee and ranged damage timing and hit reactions
    [Header("Combat Stats")]
    [Min(0)] public int damage = 1;
    [Min(0f)] public float weaponRange = 0.75f;
    [Min(0f)] public float attackCooldown = 0.8f;
    [Min(0f)] public float knockbackForce = 8f;
    [Min(0f)] public float knockbackTime = 0.12f;
    [Min(0f)] public float stunTime = 0.25f;

    // controls the player movement speed
    [Header("Movement Stats")]
    [Min(0f)] public float moveSpeed = 5f;

    // stores the health limit and current player health
    [Header("Health Stats")]
    [Min(1)] public int maxHealth = 5;
    public int currentHealth;

    // tells ui and gameplay listeners whenever a stored stat changes
    public event Action StatsChanged;

    // keeps one manager and resets current health for a new runtime session
    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
        currentHealth = maxHealth;
    }

    // applies one permanent skill effect and reports the changed stats
    public void ApplySkillUpgrade(SkillsSO.EffectType effectType, float amount)
    {
        amount = Mathf.Max(0f, amount);

        switch (effectType)
        {
            case SkillsSO.EffectType.MaxHealth:
                // added maximum health also heals by the same amount
                int healthIncrease = Mathf.Max(1, Mathf.RoundToInt(amount));
                maxHealth += healthIncrease;
                currentHealth += healthIncrease;
                break;
            case SkillsSO.EffectType.Damage:
                damage += Mathf.Max(1, Mathf.RoundToInt(amount));
                break;
            case SkillsSO.EffectType.MoveSpeed:
                moveSpeed += amount;
                break;
            case SkillsSO.EffectType.None:
                return;
            default:
                Debug.LogWarning($"Unsupported skill effect: {effectType}", this);
                return;
        }

        StatsChanged?.Invoke();
    }

    // changes health within its valid range and reports only real changes
    public int ChangeHealth(int amount)
    {
        int nextHealth = Mathf.Clamp(currentHealth + amount, 0, maxHealth);
        if (nextHealth == currentHealth)
        {
            return currentHealth;
        }

        currentHealth = nextHealth;
        StatsChanged?.Invoke();
        return currentHealth;
    }

    // applies every positive effect from one item and reports whether anything changed
    public bool TryApplyItemEffects(ItemSO itemSO)
    {
        if (itemSO == null)
        {
            return false;
        }

        int previousHealth = currentHealth;
        int previousMaxHealth = maxHealth;
        int previousDamage = damage;
        float previousMoveSpeed = moveSpeed;

        if (itemSO.maxHealthBonus > 0)
        {
            // wide arithmetic prevents integer overflow before the final limit
            long updatedMaxHealth = (long)maxHealth + itemSO.maxHealthBonus;
            maxHealth = updatedMaxHealth > int.MaxValue ? int.MaxValue : (int)updatedMaxHealth;
        }

        if (itemSO.healthRestore > 0)
        {
            long updatedHealth = (long)currentHealth + itemSO.healthRestore;
            currentHealth = updatedHealth > maxHealth ? maxHealth : (int)updatedHealth;
        }

        if (itemSO.damageBonus > 0)
        {
            long updatedDamage = (long)damage + itemSO.damageBonus;
            damage = updatedDamage > int.MaxValue ? int.MaxValue : (int)updatedDamage;
        }

        if (itemSO.speedBonus > 0)
        {
            moveSpeed = Mathf.Min(float.MaxValue, moveSpeed + itemSO.speedBonus);
        }

        bool changed = currentHealth != previousHealth ||
                       maxHealth != previousMaxHealth ||
                       damage != previousDamage ||
                       !Mathf.Approximately(moveSpeed, previousMoveSpeed);

        if (changed)
        {
            StatsChanged?.Invoke();
        }

        return changed;
    }

    // removes item effects that should last only while the item remains active
    public void RemoveTemporaryItemEffects(
        int maxHealthBonus,
        int damageBonus,
        int speedBonus)
    {
        int previousHealth = currentHealth;
        int previousMaxHealth = maxHealth;
        int previousDamage = damage;
        float previousMoveSpeed = moveSpeed;

        maxHealth = Mathf.Max(1, maxHealth - Mathf.Max(0, maxHealthBonus));
        currentHealth = Mathf.Min(currentHealth, maxHealth);
        damage = Mathf.Max(0, damage - Mathf.Max(0, damageBonus));
        moveSpeed = Mathf.Max(0f, moveSpeed - Mathf.Max(0, speedBonus));

        bool changed = currentHealth != previousHealth ||
                       maxHealth != previousMaxHealth ||
                       damage != previousDamage ||
                       !Mathf.Approximately(moveSpeed, previousMoveSpeed);

        if (changed)
        {
            StatsChanged?.Invoke();
        }
    }

    // clears singleton ownership only when the active manager is destroyed
    private void OnDestroy()
    {
        if (Instance == this)
        {
            Instance = null;
        }
    }
}
