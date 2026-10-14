using UnityEngine;

// controls enemy attack range, timing, animation, damage, and knockback
[DisallowMultipleComponent]
public class Enemy_Combat : MonoBehaviour
{
    // sets the damage, push strength, stun length, and delay between attacks
    public int damage = 1;
    public float knockbackForce = 4f;
    public float stunTime = 0.2f;
    public float attackRecovery = 0.25f;
    // defines the collider that must overlap the player before an attack can hit
    public Collider2D attackCollider;

    // stores nearby components and the active player references
    private Animator anim;
    private Enemy_Movement movement;
    private PlayerHealth playerHealth;
    private PlayerMovement playerMovement;
    private Collider2D playerCollider;
    // tracks attack state and reuses the animator key
    private bool isAttacking;
    private float nextAttackTime;
    private static readonly int IsAttackingHash = Animator.StringToHash("isAttacking");

    // gathers local components and chooses a default attack collider
    private void Awake()
    {
        anim = GetComponent<Animator>();
        movement = GetComponent<Enemy_Movement>();

        if (attackCollider == null)
        {
            attackCollider = GetComponent<CapsuleCollider2D>();
        }
    }

    // finds the active player and the components needed for attack checks
    private void Start()
    {
        GameObject playerObject = GameObject.FindGameObjectWithTag("Player");
        if (playerObject == null)
        {
            return;
        }

        playerHealth = playerObject.GetComponent<PlayerHealth>();
        playerMovement = playerObject.GetComponent<PlayerMovement>();
        playerCollider = playerObject.GetComponent<Collider2D>();
    }

    // starts an attack when the player overlaps and recovery has finished
    private void FixedUpdate()
    {
        if (movement != null && movement.IsKnockedBack)
        {
            return;
        }

        if (!isAttacking && Time.time >= nextAttackTime && IsPlayerInAttackRange())
        {
            SetAttacking(true);
        }
    }

    // applies one hit from the attack animation event
    public void Attack()
    {
        if (!isAttacking || !IsPlayerInAttackRange())
        {
            return;
        }

        if (playerMovement != null)
        {
            playerMovement.Knockback(transform, knockbackForce, stunTime);
        }

        playerHealth.ChangeHealth(-damage);
    }

    // ends the attack from the final animation event and starts recovery
    public void FinishAttack()
    {
        if (!isAttacking)
        {
            return;
        }

        SetAttacking(false);
        nextAttackTime = Time.time + attackRecovery;
    }

    // safely cancels the current attack when another effect stops the enemy
    public void InterruptAttack()
    {
        SetAttacking(false);
        nextAttackTime = Time.time + attackRecovery;
    }

    // confirms that active player and enemy colliders currently overlap
    private bool IsPlayerInAttackRange()
    {
        if (attackCollider == null || !attackCollider.enabled ||
            playerCollider == null || !playerCollider.enabled ||
            playerHealth == null || !playerHealth.gameObject.activeInHierarchy)
        {
            return false;
        }

        return attackCollider.Distance(playerCollider).isOverlapped;
    }

    // keeps animation and movement in sync with the attack state
    private void SetAttacking(bool shouldAttack)
    {
        if (isAttacking == shouldAttack)
        {
            return;
        }

        isAttacking = shouldAttack;

        if (anim != null)
        {
            anim.SetBool(IsAttackingHash, isAttacking);
        }

        if (movement != null)
        {
            movement.SetAttacking(isAttacking);
        }

    }

    // draws the configured attack shape while the enemy is selected
    private void OnDrawGizmosSelected()
    {
        Collider2D colliderToDraw = attackCollider;
        if (colliderToDraw == null)
        {
            colliderToDraw = GetComponent<CapsuleCollider2D>();
        }

        if (colliderToDraw == null)
        {
            return;
        }

        Gizmos.color = new Color(1f, 0.5f, 0f);
        Matrix4x4 previousMatrix = Gizmos.matrix;
        Gizmos.matrix = colliderToDraw.transform.localToWorldMatrix;

        if (colliderToDraw is CapsuleCollider2D capsule)
        {
            // capsules need a custom outline because gizmos have no capsule command
            DrawCapsuleGizmo(capsule);
        }
        else if (colliderToDraw is CircleCollider2D circle)
        {
            Gizmos.DrawWireSphere(circle.offset, circle.radius);
        }
        else if (colliderToDraw is BoxCollider2D box)
        {
            Gizmos.DrawWireCube(box.offset, box.size);
        }
        else
        {
            Gizmos.matrix = Matrix4x4.identity;
            Gizmos.DrawWireCube(colliderToDraw.bounds.center, colliderToDraw.bounds.size);
        }

        Gizmos.matrix = previousMatrix;
    }

    // builds a capsule outline from two circles and two connecting lines
    private static void DrawCapsuleGizmo(CapsuleCollider2D capsule)
    {
        Vector2 center = capsule.offset;
        Vector2 size = capsule.size;

        if (capsule.direction == CapsuleDirection2D.Horizontal)
        {
            float radius = size.y * 0.5f;
            float halfSegment = Mathf.Max(0f, (size.x - size.y) * 0.5f);
            Vector3 leftCenter = center + Vector2.left * halfSegment;
            Vector3 rightCenter = center + Vector2.right * halfSegment;

            Gizmos.DrawWireSphere(leftCenter, radius);
            Gizmos.DrawWireSphere(rightCenter, radius);
            Gizmos.DrawLine(leftCenter + Vector3.up * radius, rightCenter + Vector3.up * radius);
            Gizmos.DrawLine(leftCenter + Vector3.down * radius, rightCenter + Vector3.down * radius);
            return;
        }

        float verticalRadius = size.x * 0.5f;
        float verticalHalfSegment = Mathf.Max(0f, (size.y - size.x) * 0.5f);
        Vector3 bottomCenter = center + Vector2.down * verticalHalfSegment;
        Vector3 topCenter = center + Vector2.up * verticalHalfSegment;

        Gizmos.DrawWireSphere(bottomCenter, verticalRadius);
        Gizmos.DrawWireSphere(topCenter, verticalRadius);
        Gizmos.DrawLine(bottomCenter + Vector3.left * verticalRadius, topCenter + Vector3.left * verticalRadius);
        Gizmos.DrawLine(bottomCenter + Vector3.right * verticalRadius, topCenter + Vector3.right * verticalRadius);
    }

    // clears attack state when the enemy stops running
    private void OnDisable()
    {
        SetAttacking(false);
    }
}
