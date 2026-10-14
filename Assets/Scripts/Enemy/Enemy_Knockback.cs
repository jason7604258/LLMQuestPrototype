using System.Collections;
using UnityEngine;

// pushes an enemy away from a hit and pauses movement for the stun time
[DisallowMultipleComponent]
[RequireComponent(typeof(Rigidbody2D))]
[RequireComponent(typeof(Enemy_Movement))]
public class Enemy_Knockback : MonoBehaviour
{
    // connects physics, movement, combat, and the active knockback timer
    private Rigidbody2D rb;
    private Enemy_Movement movement;
    private Enemy_Combat combat;
    private Coroutine knockbackRoutine;

    // gathers the local components needed for knockback
    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
        movement = GetComponent<Enemy_Movement>();
        combat = GetComponent<Enemy_Combat>();
    }

    // restarts knockback from the newest hit and interrupts any attack
    public void Knockback(Transform source, float force, float knockbackTime, float stunTime)
    {
        if (source == null)
        {
            return;
        }

        if (knockbackRoutine != null)
        {
            StopCoroutine(knockbackRoutine);
        }

        movement.SetKnockedBack(true);

        if (combat != null)
        {
            combat.InterruptAttack();
        }

        Vector2 direction = ((Vector2)transform.position - (Vector2)source.position).normalized;
        if (direction.sqrMagnitude < 0.01f)
        {
            // overlapping objects use a safe right facing direction
            direction = Vector2.right;
        }

        rb.linearVelocity = direction * force;
        knockbackRoutine = StartCoroutine(
            KnockbackAndStun(Mathf.Max(0f, knockbackTime), Mathf.Max(0f, stunTime)));
    }

    // stops the push first and restores movement after the remaining stun
    private IEnumerator KnockbackAndStun(float knockbackTime, float stunTime)
    {
        yield return new WaitForSeconds(knockbackTime);
        rb.linearVelocity = Vector2.zero;

        yield return new WaitForSeconds(stunTime);
        movement.SetKnockedBack(false);
        knockbackRoutine = null;
    }

    // clears velocity and movement locks when the enemy stops running
    private void OnDisable()
    {
        knockbackRoutine = null;

        if (rb != null)
        {
            rb.linearVelocity = Vector2.zero;
        }

        if (movement != null)
        {
            movement.SetKnockedBack(false);
        }
    }
}
