using UnityEngine;

// controls one arrow from launch until it hits a target or expires
[DisallowMultipleComponent]
[RequireComponent(typeof(Rigidbody2D))]
[RequireComponent(typeof(Collider2D))]
public class Arrow : MonoBehaviour
{
    // controls how the arrow moves and how long it stays in the scene
    [Header("Flight")]
    [SerializeField] private Rigidbody2D rb;
    [SerializeField] private Collider2D projectileCollider;
    [Min(0f)] [SerializeField] private float speed = 12f;
    [Min(0.01f)] [SerializeField] private float lifeTime = 2f;

    // limits damage to enemies and embedding to solid obstacles
    [Header("Targets")]
    [SerializeField] private LayerMask enemyLayer;
    [SerializeField] private LayerMask obstacleLayer;

    // changes the arrow image after it becomes stuck in a target
    [Header("Embedded Visual")]
    [SerializeField] private SpriteRenderer spriteRenderer;
    [SerializeField] private Sprite buriedSprite;

    // stores the values copied from the player when this arrow is fired
    private Vector2 direction = Vector2.right;
    private Transform owner;
    private int damage;
    private float knockbackForce;
    private float knockbackTime;
    private float stunTime;
    private bool initialized;
    private bool hasHit;

    // fills common references when the component is added or reset in the inspector
    private void Reset()
    {
        rb = GetComponent<Rigidbody2D>();
        projectileCollider = GetComponent<Collider2D>();
        spriteRenderer = GetComponent<SpriteRenderer>();
        enemyLayer = LayerMask.GetMask("Enemy");
        obstacleLayer = LayerMask.GetMask("Default");
    }

    // repairs missing references and prepares the rigidbody for fast movement
    private void Awake()
    {
        if (rb == null)
        {
            rb = GetComponent<Rigidbody2D>();
        }

        if (projectileCollider == null)
        {
            projectileCollider = GetComponent<Collider2D>();
        }

        if (spriteRenderer == null)
        {
            spriteRenderer = GetComponent<SpriteRenderer>();
        }

        if (enemyLayer.value == 0)
        {
            enemyLayer = LayerMask.GetMask("Enemy");
        }

        if (obstacleLayer.value == 0)
        {
            obstacleLayer = LayerMask.GetMask("Default");
        }

        if (rb != null)
        {
            rb.gravityScale = 0f;
            rb.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
        }
    }

    // copies one shot into the arrow and starts its flight once
    public void Initialize(
        Vector2 shootDirection,
        int projectileDamage,
        float force,
        float forceDuration,
        float targetStunTime,
        Transform projectileOwner,
        LayerMask targetLayer)
    {
        if (initialized)
        {
            // repeated setup could restart the same arrow with different values
            return;
        }

        initialized = true;
        direction = shootDirection.sqrMagnitude > 0.001f
            ? shootDirection.normalized
            : Vector2.right;
        damage = Mathf.Max(0, projectileDamage);
        knockbackForce = Mathf.Max(0f, force);
        knockbackTime = Mathf.Max(0f, forceDuration);
        stunTime = Mathf.Max(0f, targetStunTime);
        owner = projectileOwner;

        if (targetLayer.value != 0)
        {
            enemyLayer = targetLayer;
        }

        IgnoreOwnerCollisions();
        StartFlight();
    }

    // points the arrow forward, gives it speed, and schedules cleanup
    private void StartFlight()
    {
        RotateArrow();

        if (rb != null)
        {
            rb.linearVelocity = direction * speed;
        }

        Destroy(gameObject, lifeTime);
    }

    // turns the arrow sprite to match its travel direction
    private void RotateArrow()
    {
        float angle = Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg;
        transform.rotation = Quaternion.Euler(0f, 0f, angle);
    }

    // prevents the fired arrow from colliding with the player who owns it
    private void IgnoreOwnerCollisions()
    {
        if (owner == null || projectileCollider == null)
        {
            return;
        }

        Collider2D[] ownerColliders = owner.GetComponentsInChildren<Collider2D>();
        foreach (Collider2D ownerCollider in ownerColliders)
        {
            if (ownerCollider != null)
            {
                Physics2D.IgnoreCollision(projectileCollider, ownerCollider, true);
            }
        }
    }

    // sends rigidbody collisions through the shared hit rules
    private void OnCollisionEnter2D(Collision2D collision)
    {
        HandleCollision(collision.collider);
    }

    // applies damage or stops the arrow based on the object that was hit
    private void HandleCollision(Collider2D hitCollider)
    {
        if (hasHit || hitCollider == null)
        {
            return;
        }

        if (owner != null && hitCollider.transform.IsChildOf(owner))
        {
            return;
        }

        Enemy_Health enemyHealth = hitCollider.GetComponentInParent<Enemy_Health>();
        if (enemyHealth != null && IsInEnemyLayer(hitCollider, enemyHealth))
        {
            // damage is applied once before the arrow becomes part of the target
            hasHit = true;
            enemyHealth.ChangeHealth(-damage);

            Enemy_Knockback enemyKnockback = enemyHealth.GetComponent<Enemy_Knockback>();
            if (enemyHealth.currentHealth > 0 && enemyKnockback != null && knockbackForce > 0f)
            {
                enemyKnockback.Knockback(
                    owner != null ? owner : transform,
                    knockbackForce,
                    knockbackTime,
                    stunTime);
            }

            AttachToTarget(enemyHealth.transform);
            return;
        }

        if (IsLayerInMask(hitCollider.gameObject.layer, obstacleLayer))
        {
            // configured obstacles keep the arrow visible after impact
            hasHit = true;
            AttachToTarget(hitCollider.transform);
            return;
        }

        // other solid colliders stop the arrow without keeping it visible
        hasHit = true;
        Destroy(gameObject);
    }

    // freezes the arrow, disables more hits, and follows the struck object
    private void AttachToTarget(Transform target)
    {
        if (spriteRenderer != null && buriedSprite != null)
        {
            spriteRenderer.sprite = buriedSprite;
        }

        if (rb != null)
        {
            rb.linearVelocity = Vector2.zero;
            rb.angularVelocity = 0f;
            rb.bodyType = RigidbodyType2D.Kinematic;
        }

        // disabling the collider prevents repeated damage and unwanted pushing
        if (projectileCollider != null)
        {
            projectileCollider.enabled = false;
        }

        if (target != null)
        {
            transform.SetParent(target, true);
        }
    }

    // accepts the layer from either the hit collider or its health object
    private bool IsInEnemyLayer(Collider2D hitCollider, Enemy_Health enemyHealth)
    {
        int colliderLayerMask = 1 << hitCollider.gameObject.layer;
        int healthLayerMask = 1 << enemyHealth.gameObject.layer;
        return (enemyLayer.value & colliderLayerMask) != 0 ||
               (enemyLayer.value & healthLayerMask) != 0;
    }

    // checks whether one layer belongs to a configured layer mask
    private static bool IsLayerInMask(int layer, LayerMask layerMask)
    {
        return (layerMask.value & (1 << layer)) != 0;
    }
}
