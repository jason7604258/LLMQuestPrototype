using System.Collections;
using UnityEngine;

// reads player input, moves the rigidbody, and keeps aim and facing in sync
[DisallowMultipleComponent]
[RequireComponent(typeof(Rigidbody2D))]
public class PlayerMovement : MonoBehaviour
{
    // connects movement to player physics animation and equipped attacks
    public Rigidbody2D rb;
    public Animator anim;
    public Player_Combat playerCombat;
    [SerializeField] private Player_bow playerBow;
    public string attackButton = "Slash";
    public int faceDirection = 1;

    // exposes the last useful aim and current stun state to weapon scripts
    public Vector2 AimDirection { get; private set; } = Vector2.right;
    public bool IsStunned => isStunned;

    // stores input and temporary knockback state between update loops
    private Vector2 movementInput;
    private bool isStunned;
    private Coroutine knockbackRoutine;
    private StatsManager stats;

    // fills common references when the component is added or reset in the inspector
    private void Reset()
    {
        rb = GetComponent<Rigidbody2D>();
        anim = GetComponent<Animator>();
        playerCombat = GetComponent<Player_Combat>();
        playerBow = GetComponent<Player_bow>();
    }

    // repairs missing references and prepares the rigidbody for top down movement
    private void Awake()
    {
        stats = StatsManager.Instance;

        if (rb == null)
        {
            rb = GetComponent<Rigidbody2D>();
        }

        if (anim == null)
        {
            anim = GetComponent<Animator>();
        }

        if (playerCombat == null)
        {
            playerCombat = GetComponent<Player_Combat>();
        }

        if (playerBow == null)
        {
            playerBow = GetComponent<Player_bow>();
        }

        faceDirection = transform.localScale.x < 0f ? -1 : 1;
        AimDirection = Vector2.right * faceDirection;

        if (rb != null)
        {
            rb.gravityScale = 0f;
            rb.freezeRotation = true;
            rb.interpolation = RigidbodyInterpolation2D.Interpolate;
        }
    }

    // reads input and updates visuals once per rendered frame
    private void Update()
    {
        if (isStunned)
        {
            // stunned players keep their knockback velocity but cannot add input
            movementInput = Vector2.zero;
            UpdateAnimator();
            return;
        }

        ReadCombatInput();
        ReadMovementInput();
        UpdateFacing();
        UpdateAnimator();
    }

    // applies movement through physics at a steady rate
    private void FixedUpdate()
    {
        if (rb == null || isStunned)
        {
            return;
        }

        if (playerBow != null && playerBow.isActiveAndEnabled && playerBow.IsShooting)
        {
            // shooting keeps the player still until the bow release finishes
            rb.linearVelocity = Vector2.zero;
            return;
        }

        if (stats == null)
        {
            return;
        }

        rb.linearVelocity = movementInput * stats.moveSpeed;
    }

    // clears movement and temporary state when the component stops running
    private void OnDisable()
    {
        isStunned = false;
        knockbackRoutine = null;

        if (rb != null)
        {
            rb.linearVelocity = Vector2.zero;
        }
    }

    // pushes the player away from a source and blocks input for a short time
    public void Knockback(Transform source, float force, float stunTime)
    {
        if (rb == null || source == null)
        {
            return;
        }

        if (knockbackRoutine != null)
        {
            StopCoroutine(knockbackRoutine);
        }

        Vector2 direction = ((Vector2)transform.position - (Vector2)source.position).normalized;
        if (direction.sqrMagnitude < 0.01f)
        {
            // overlapping objects use the current facing as a safe direction
            direction = Vector2.right * faceDirection;
        }

        isStunned = true;
        movementInput = Vector2.zero;
        rb.linearVelocity = direction * force;
        knockbackRoutine = StartCoroutine(KnockbackCounter(stunTime));
    }

    // ends knockback after the requested stun time
    private IEnumerator KnockbackCounter(float stunTime)
    {
        yield return new WaitForSeconds(Mathf.Max(0f, stunTime));

        rb.linearVelocity = Vector2.zero;
        isStunned = false;
        knockbackRoutine = null;
    }

    // reads both movement axes and keeps diagonal movement at normal speed
    private void ReadMovementInput()
    {
        float horizontal = Input.GetAxisRaw("Horizontal");
        float vertical = Input.GetAxisRaw("Vertical");

        movementInput = new Vector2(horizontal, vertical);

        if (movementInput.sqrMagnitude > 1f)
        {
            movementInput.Normalize();
        }

        if (movementInput.sqrMagnitude > 0.001f)
        {
            // the last nonzero direction remains available while standing still
            AimDirection = movementInput.normalized;
        }
    }

    // starts a melee attack when that equipment component is active
    private void ReadCombatInput()
    {
        if (playerCombat != null &&
            playerCombat.isActiveAndEnabled &&
            Input.GetButtonDown(attackButton))
        {
            playerCombat.Attack();
        }
    }

    // flips the character only when horizontal input crosses sides
    private void UpdateFacing()
    {
        if ((movementInput.x > 0.01f && faceDirection < 0) ||
            (movementInput.x < -0.01f && faceDirection > 0))
        {
            Flip();
        }
    }

    // sends movement strength to the animator
    private void UpdateAnimator()
    {
        if (anim == null)
        {
            return;
        }

        anim.SetFloat("horizontal", Mathf.Abs(movementInput.x));
        anim.SetFloat("vertical", Mathf.Abs(movementInput.y));
    }

    // mirrors the character without changing its authored scale size
    private void Flip()
    {
        faceDirection *= -1;

        Vector3 scale = transform.localScale;
        scale.x = Mathf.Approximately(scale.x, 0f) ? faceDirection : Mathf.Abs(scale.x) * faceDirection;
        transform.localScale = scale;
    }
}
