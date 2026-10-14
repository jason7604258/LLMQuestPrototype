using System.Collections.Generic;
using UnityEngine;

// controls melee attack timing, animation, damage, and knockback
[DisallowMultipleComponent]
[RequireComponent(typeof(Animator))]
public class Player_Combat : MonoBehaviour
{
    // connects the attack animation, hit position, and valid enemy layers
    public Animator anim;
    public Transform attackPoint;
    public LayerMask enemyLayer;

    // stores the animator key and current attack timing state
    private static readonly int IsAttackingHash = Animator.StringToHash("isAttacking");
    private float cooldownTimer;
    private bool isAttacking;
    // stores the shared player stats used by every attack
    private StatsManager stats;

    // fills common references when the component is added or reset in the inspector
    private void Reset()
    {
        anim = GetComponent<Animator>();
        attackPoint = transform.Find("AttackPoint");
        enemyLayer = LayerMask.GetMask("Enemy");
    }

    // repairs missing references and finds the shared stats source
    private void Awake()
    {
        stats = StatsManager.Instance;

        if (anim == null)
        {
            anim = GetComponent<Animator>();
        }

        if (attackPoint == null)
        {
            attackPoint = transform.Find("AttackPoint");
        }

        if (enemyLayer.value == 0)
        {
            enemyLayer = LayerMask.GetMask("Enemy");
        }
    }

    // counts down the delay before another attack can begin
    private void Update()
    {
        if (cooldownTimer > 0f)
        {
            cooldownTimer = Mathf.Max(0f, cooldownTimer - Time.deltaTime);
        }
    }

    // begins one melee attack when the player is ready
    public void Attack()
    {
        if (anim == null || stats == null || isAttacking || cooldownTimer > 0f)
        {
            return;
        }

        isAttacking = true;
        cooldownTimer = stats.attackCooldown;
        anim.SetBool(IsAttackingHash, true);
    }

    // ends the attack from the final animation event
    public void FinishAttack()
    {
        isAttacking = false;

        if (anim != null)
        {
            anim.SetBool(IsAttackingHash, false);
        }
    }

    // applies one hit from the damage animation event
    public void DealDamage()
    {
        if (!isAttacking || attackPoint == null || stats == null)
        {
            return;
        }

        Collider2D[] hits = Physics2D.OverlapCircleAll(
            attackPoint.position,
            stats.weaponRange,
            enemyLayer);

        HashSet<Enemy_Health> damagedEnemies = new HashSet<Enemy_Health>();

        // one enemy may have several colliders but should only take one hit
        foreach (Collider2D hit in hits)
        {
            if (hit.isTrigger)
            {
                continue;
            }

            Enemy_Health enemyHealth = hit.GetComponentInParent<Enemy_Health>();
            if (enemyHealth != null && damagedEnemies.Add(enemyHealth))
            {
                enemyHealth.ChangeHealth(-stats.damage);

                Enemy_Knockback enemyKnockback = enemyHealth.GetComponent<Enemy_Knockback>();
                if (enemyHealth.currentHealth > 0 && enemyKnockback != null)
                {
                    enemyKnockback.Knockback(
                        transform,
                        stats.knockbackForce,
                        stats.knockbackTime,
                        stats.stunTime);
                }
            }
        }
    }

    // draws the current attack range around the attack point in the editor
    private void OnDrawGizmosSelected()
    {
        if (attackPoint == null)
        {
            return;
        }

        StatsManager statsManager = StatsManager.Instance;
        if (statsManager == null)
        {
            // edit mode may have a manager in the scene without an active singleton
            statsManager = FindAnyObjectByType<StatsManager>();
        }

        if (statsManager == null)
        {
            return;
        }

        Gizmos.color = Color.red;
        Gizmos.DrawWireSphere(attackPoint.position, statsManager.weaponRange);
    }

    // clears an unfinished attack when this equipment mode is disabled
    private void OnDisable()
    {
        isAttacking = false;
        cooldownTimer = 0f;

        if (anim != null)
        {
            anim.SetBool(IsAttackingHash, false);
        }
    }
}
