using System;
using UnityEngine;

// stores enemy health and reports quest progress and experience on death
public class Enemy_Health : MonoBehaviour
{
    // reports normal enemy and boss deaths to quest systems
    public static event Action<string> EnemyKilled;
    public static event Action<string> BossKilled;

    // identifies which quest target this enemy represents
    [Header("Quest Identity")]
    [SerializeField] private string enemyId = "enemy_torch";
    [SerializeField] private string bossId = string.Empty;

    // sets starting health and the experience granted on death
    [Header("Health and Rewards")]
    [Min(1)] public int maxHealth = 3;
    public int currentHealth;
    [Min(0)] public int experienceReward = 2;

    // exposes cleaned quest identifiers without allowing outside replacement
    public string EnemyId => enemyId;
    public string BossId => bossId;

    // blocks repeated rewards while destruction waits for the end of the frame
    private bool isDead;

    // cleans identifiers and resets health when the enemy is created
    private void Awake()
    {
        enemyId = enemyId?.Trim();
        bossId = bossId?.Trim();
        maxHealth = Mathf.Max(1, maxHealth);
        currentHealth = maxHealth;
    }

    // applies a health change and starts death once health reaches zero
    public void ChangeHealth(int amount)
    {
        if (isDead)
        {
            return;
        }

        currentHealth = Mathf.Clamp(currentHealth + amount, 0, maxHealth);

        if (currentHealth <= 0)
        {
            Die();
        }
    }

    // reports the correct quest event, grants experience, and removes the enemy
    private void Die()
    {
        isDead = true;

        bool isBoss = !string.IsNullOrWhiteSpace(bossId);

        if (isBoss)
        {
            // a boss identifier takes priority over the normal enemy identifier
            BossKilled?.Invoke(bossId);
        }
        else if (!string.IsNullOrWhiteSpace(enemyId))
        {
            EnemyKilled?.Invoke(enemyId);
        }
        else
        {
            Debug.LogWarning(
                $"Enemy '{name}' died without a quest enemy ID.",
                this);
        }

        if (ExpManager.Instance != null)
        {
            ExpManager.Instance.GainExperience(experienceReward);
        }

        Destroy(gameObject);
    }
}
