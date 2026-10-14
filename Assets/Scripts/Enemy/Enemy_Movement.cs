using UnityEngine;

// makes an enemy find the player, chase within range, and face the right direction
[DisallowMultipleComponent]
[RequireComponent(typeof(Rigidbody2D))]
public class Enemy_Movement : MonoBehaviour
{
    // controls chase speed, detection size, and stopping distance
    public float speed = 3f;
    public float detectionRange = 5f;
    public float stopDistance = 0.6f;
    public Collider2D detectionCollider;
    // controls the current facing and the direction drawn by the source sprite
    public int faceDirection = 1;
    public bool spriteFacesRight = true;

    // stores local physics and animation components with the current player target
    private Rigidbody2D rb;
    private Animator anim;
    public Transform player;

    // keeps player collision, original scale, and movement state between physics steps
    private Collider2D playerCollider;
    private Vector3 baseLocalScale;
    private EnemyState enemyState = EnemyState.None;
    private bool isAttacking;
    private bool isKnockedBack;
    // stores small shared limits and animator keys
    private const float FacingThreshold = 0.01f;
    private const float MinimumScale = 0.0001f;
    private static readonly int IsIdleHash = Animator.StringToHash("isIdle");
    private static readonly int IsChasingHash = Animator.StringToHash("isChasing");

    // fills the detection trigger when the component is added or reset in the inspector
    private void Reset()
    {
        detectionCollider = GetComponent<CircleCollider2D>();
        SynchronizeDetectionCollider();
    }

    // keeps editor values valid and updates the detection trigger while editing
    private void OnValidate()
    {
        detectionRange = Mathf.Max(0f, detectionRange);
        stopDistance = Mathf.Clamp(stopDistance, 0f, detectionRange);

        if (detectionCollider == null)
        {
            detectionCollider = GetComponent<CircleCollider2D>();
        }

        SynchronizeDetectionCollider();
    }

    // prepares physics, finds the player, and sets the initial facing and state
    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
        anim = GetComponent<Animator>();
        baseLocalScale = transform.localScale;
        baseLocalScale.x = Mathf.Abs(baseLocalScale.x);

        if (detectionCollider == null)
        {
            detectionCollider = GetComponent<CircleCollider2D>();
        }

        SynchronizeDetectionCollider();
        ResolvePlayerReference();

        rb.gravityScale = 0f;
        rb.freezeRotation = true;
        rb.interpolation = RigidbodyInterpolation2D.Interpolate;

        if (Mathf.Abs(transform.localScale.x) > FacingThreshold)
        {
            // the authored scale decides the initial logical facing
            faceDirection = (transform.localScale.x > 0f) == spriteFacesRight ? 1 : -1;
        }
        else
        {
            faceDirection = faceDirection < 0 ? -1 : 1;
        }

        ApplyFacingDirection();
        ChangeState(EnemyState.Idle);
    }

    // refreshes the player reference whenever the enemy becomes active
    private void OnEnable()
    {
        ResolvePlayerReference();
    }

    // chooses idle or chase movement during each physics step
    private void FixedUpdate()
    {
        if (isKnockedBack)
        {
            return;
        }

        if (!ResolvePlayerReference())
        {
            // enemies stay still when no active player exists in the scene
            rb.linearVelocity = Vector2.zero;
            ChangeState(EnemyState.Idle);
            return;
        }

        Vector2 toPlayer = player.position - transform.position;
        bool canDetectPlayer = CanDetectPlayer();

        if (isAttacking)
        {
            // attack animation owns the enemy until combat clears this state
            rb.linearVelocity = Vector2.zero;
            ChangeState(EnemyState.Idle);
            return;
        }

        if (canDetectPlayer)
        {
            UpdateFacingDirection(toPlayer.x);
        }

        if (!canDetectPlayer || toPlayer.magnitude <= stopDistance)
        {
            // stopping near the player prevents constant pushing and overlap
            rb.linearVelocity = Vector2.zero;
            ChangeState(EnemyState.Idle);
            return;
        }

        rb.linearVelocity = toPlayer.normalized * speed;
        ChangeState(EnemyState.Chasing);
    }

    // finds the active player after scene changes or duplicate player cleanup
    private bool ResolvePlayerReference()
    {
        if (player != null && player.gameObject.activeInHierarchy)
        {
            if (playerCollider == null)
            {
                playerCollider = player.GetComponent<Collider2D>();
            }

            return true;
        }

        player = null;
        playerCollider = null;

        GameObject playerObject = GameObject.FindGameObjectWithTag("Player");
        if (playerObject == null)
        {
            return false;
        }

        player = playerObject.transform;
        playerCollider = playerObject.GetComponent<Collider2D>();
        return true;
    }

    // keeps a circular trigger centred with the requested world detection size
    private void SynchronizeDetectionCollider()
    {
        if (!(detectionCollider is CircleCollider2D circleCollider))
        {
            return;
        }

        circleCollider.isTrigger = true;
        circleCollider.offset = Vector2.zero;

        Vector3 worldScale = transform.lossyScale;
        // dividing by the largest scale keeps the final world radius predictable
        float largestScale = Mathf.Max(
            Mathf.Abs(worldScale.x),
            Mathf.Abs(worldScale.y));
        circleCollider.radius = largestScale > MinimumScale
            ? detectionRange / largestScale
            : detectionRange;
    }

    // checks the trigger first and falls back to distance when no trigger is active
    private bool CanDetectPlayer()
    {
        if (detectionCollider != null && detectionCollider.enabled)
        {
            if (playerCollider != null && detectionCollider.IsTouching(playerCollider))
            {
                return true;
            }

            if (detectionCollider.OverlapPoint(player.position))
            {
                return true;
            }

            return false;
        }

        return Vector2.Distance(transform.position, player.position) <= detectionRange;
    }

    // changes facing only after useful horizontal movement appears
    private void UpdateFacingDirection(float horizontalDirection)
    {
        if (Mathf.Abs(horizontalDirection) <= FacingThreshold)
        {
            return;
        }

        int newFaceDirection = horizontalDirection > 0f ? 1 : -1;
        if (newFaceDirection == faceDirection)
        {
            return;
        }

        faceDirection = newFaceDirection;
        ApplyFacingDirection();
    }

    // mirrors the saved original scale to match the logical facing
    private void ApplyFacingDirection()
    {
        Vector3 scale = baseLocalScale;
        int scaleDirection = spriteFacesRight ? faceDirection : -faceDirection;
        scale.x *= scaleDirection;
        transform.localScale = scale;
    }

    // lets combat stop or release movement during an attack
    public void SetAttacking(bool attacking)
    {
        isAttacking = attacking;
    }

    // lets knockback pause chasing until the stun finishes
    public void SetKnockedBack(bool knockedBack)
    {
        isKnockedBack = knockedBack;

        if (isKnockedBack)
        {
            ChangeState(EnemyState.Idle);
        }
    }

    // exposes knockback state to combat without allowing direct replacement
    public bool IsKnockedBack => isKnockedBack;

    // changes animator flags only when the movement state really changes
    private void ChangeState(EnemyState newState)
    {
        if (enemyState == newState)
        {
            return;
        }

        enemyState = newState;

        if (anim == null)
        {
            return;
        }

        anim.SetBool(IsIdleHash, enemyState == EnemyState.Idle);
        anim.SetBool(IsChasingHash, enemyState == EnemyState.Chasing);
    }

    // clears temporary movement when the enemy stops running
    private void OnDisable()
    {
        isKnockedBack = false;

        if (rb != null)
        {
            rb.linearVelocity = Vector2.zero;
        }
    }

    // lists the movement states represented in the animator
    private enum EnemyState
    {
        None,
        Idle,
        Chasing
    }
}
