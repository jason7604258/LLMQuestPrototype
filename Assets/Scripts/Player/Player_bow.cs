using System.Collections;
using UnityEngine;
using UnityEngine.EventSystems;

// controls bow input, shoot animation, and arrow creation
[DisallowMultipleComponent]
[RequireComponent(typeof(PlayerMovement))]
public class Player_bow : MonoBehaviour
{
    // connects the launch point, arrow prefab, and valid enemy layers
    [Header("Projectile")]
    [SerializeField] private Transform launchPoint;
    [SerializeField] private Arrow arrowPrefab;
    [SerializeField] private LayerMask enemyLayer;

    // names the input action used to shoot
    [Header("Input")]
    [SerializeField] private string shootButton = "Shoot";

    // connects movement and animation used while aiming and shooting
    [Header("References")]
    [SerializeField] private PlayerMovement playerMovement;
    [SerializeField] private Animator animator;

    // stores animator keys once so repeated updates do not rebuild them
    private static readonly int AimHorizontal = Animator.StringToHash("aimHorizontal");
    private static readonly int AimVertical = Animator.StringToHash("aimVertical");
    private static readonly int IsShootingHash = Animator.StringToHash("isShooting");

    // keeps the fallback animation timer close to the authored clip length
    private const float ShootAnimationDuration = 0.6f;

    // stores shared stats, timing, and the values captured for the next arrow
    private StatsManager stats;
    private Coroutine shootingAnimationRoutine;
    private float cooldownTimer;
    private Vector2 pendingAimDirection;
    private int pendingDamage;
    private float pendingKnockbackForce;
    private float pendingKnockbackTime;
    private float pendingStunTime;
    private bool hasPendingShot;
    private bool warnedAboutSetup;

    // reports whether movement should pause for the current shot
    public bool IsShooting { get; private set; }

    // fills common references when the component is added or reset in the inspector
    private void Reset()
    {
        playerMovement = GetComponent<PlayerMovement>();
        animator = GetComponent<Animator>();
        launchPoint = transform.Find("LaunchPoint");
        if (launchPoint == null)
        {
            launchPoint = transform.Find("AttackPoint");
        }

        enemyLayer = LayerMask.GetMask("Enemy");
    }

    // repairs missing references and chooses a safe launch point
    private void Awake()
    {
        stats = StatsManager.Instance;

        if (playerMovement == null)
        {
            playerMovement = GetComponent<PlayerMovement>();
        }

        if (animator == null)
        {
            animator = GetComponent<Animator>();
        }

        if (launchPoint == null)
        {
            launchPoint = transform.Find("LaunchPoint");
        }

        if (launchPoint == null)
        {
            launchPoint = transform.Find("AttackPoint");
        }

        if (launchPoint == null)
        {
            // the player transform keeps shooting usable without a child launch point
            launchPoint = transform;
        }

        if (enemyLayer.value == 0)
        {
            enemyLayer = LayerMask.GetMask("Enemy");
        }
    }

    // counts down cooldown and listens for shooting input during gameplay
    private void Update()
    {
        if (cooldownTimer > 0f)
        {
            cooldownTimer = Mathf.Max(0f, cooldownTimer - Time.deltaTime);
        }

        if (Time.timeScale <= 0f || playerMovement == null || playerMovement.IsStunned)
        {
            return;
        }

        if (Input.GetButtonDown(shootButton))
        {
            // right clicking inventory drops an item and should not also fire an arrow
            // keyboard and controller shooting still work while the pointer is over ui
            bool rightClickOverUI = Input.GetMouseButtonDown(1) &&
                                    EventSystem.current != null &&
                                    EventSystem.current.IsPointerOverGameObject();

            if (!rightClickOverUI)
            {
                Shoot();
            }
        }
    }

    // captures one valid shot and begins its release animation
    public bool Shoot()
    {
        if (cooldownTimer > 0f || hasPendingShot)
        {
            return false;
        }

        if (stats == null)
        {
            stats = StatsManager.Instance;
        }

        if (arrowPrefab == null || stats == null)
        {
            // missing required setup leaves cooldown and animation unchanged
            WarnAboutMissingSetup();
            return false;
        }

        Vector2 aimDirection = ReadAimDirectionForShot();

        if (aimDirection.sqrMagnitude < 0.001f)
        {
            aimDirection = Vector2.right;
        }

        // capture stats now so later changes cannot alter an arrow already being drawn
        // the animation event releases these saved values at the bow release frame
        pendingAimDirection = aimDirection.normalized;
        pendingDamage = stats.damage;
        pendingKnockbackForce = stats.knockbackForce;
        pendingKnockbackTime = stats.knockbackTime;
        pendingStunTime = stats.stunTime;
        hasPendingShot = true;
        IsShooting = true;

        PlayShootAnimation(aimDirection);
        cooldownTimer = Mathf.Max(0f, stats.attackCooldown);
        return true;
    }

    // releases one arrow from the directional shoot animation event
    // consuming the pending shot first prevents duplicate blend tree events
    public void ReleaseArrow()
    {
        if (!hasPendingShot)
        {
            return;
        }

        hasPendingShot = false;
        IsShooting = false;

        if (arrowPrefab == null)
        {
            // the pending shot is cleared even if its prefab was removed during animation
            WarnAboutMissingSetup();
            return;
        }

        Arrow arrow = Instantiate(
            arrowPrefab,
            GetLaunchPosition(pendingAimDirection),
            Quaternion.identity);

        arrow.Initialize(
            pendingAimDirection,
            pendingDamage,
            pendingKnockbackForce,
            pendingKnockbackTime,
            pendingStunTime,
            transform,
            enemyLayer);
    }

    // sets aim values and keeps a timer as a backup for animation events
    private void PlayShootAnimation(Vector2 aimDirection)
    {
        if (animator == null)
        {
            // shooting still works immediately when the animator is missing
            ReleaseArrow();
            IsShooting = false;
            return;
        }

        // the character transform handles left and right flipping
        // the blend tree only needs the horizontal aim size
        animator.SetFloat(AimHorizontal, Mathf.Abs(aimDirection.x));
        animator.SetFloat(AimVertical, aimDirection.y);
        animator.SetBool(IsShootingHash, true);

        if (shootingAnimationRoutine != null)
        {
            StopCoroutine(shootingAnimationRoutine);
        }

        shootingAnimationRoutine = StartCoroutine(FinishShootAnimation());
    }

    // chooses current input, remembered aim, or a safe right facing fallback
    private Vector2 ReadAimDirectionForShot()
    {
        // reading axes with the button avoids using a direction from the previous frame
        Vector2 inputDirection = new Vector2(
            Input.GetAxisRaw("Horizontal"),
            Input.GetAxisRaw("Vertical"));

        if (inputDirection.sqrMagnitude > 0.001f)
        {
            return inputDirection.normalized;
        }

        if (playerMovement != null &&
            playerMovement.AimDirection.sqrMagnitude > 0.001f)
        {
            return playerMovement.AimDirection.normalized;
        }

        return Vector2.right;
    }

    // ends the animation and releases an arrow if its event did not run
    private IEnumerator FinishShootAnimation()
    {
        yield return new WaitForSeconds(ShootAnimationDuration);

        // a normal animation event has already consumed the pending shot
        ReleaseArrow();

        if (animator != null)
        {
            animator.SetBool(IsShootingHash, false);
        }

        IsShooting = false;
        shootingAnimationRoutine = null;
    }

    // places the arrow along the aim direction using the authored launch distance
    private Vector3 GetLaunchPosition(Vector2 aimDirection)
    {
        Vector3 playerPosition = transform.position;
        float launchDistance = 0.65f;

        if (launchPoint != null && launchPoint != transform)
        {
            launchDistance = Vector2.Distance(playerPosition, launchPoint.position);
        }

        // use the child distance but place the arrow in the actual aim direction
        Vector3 spawnPosition = playerPosition +
                                (Vector3)(aimDirection.normalized * launchDistance);
        spawnPosition.z = launchPoint != null ? launchPoint.position.z : playerPosition.z;
        return spawnPosition;
    }

    // reports missing setup once without filling the console every frame
    private void WarnAboutMissingSetup()
    {
        if (warnedAboutSetup)
        {
            return;
        }

        warnedAboutSetup = true;
        Debug.LogWarning(
            "Player_bow cannot shoot because the Arrow prefab or StatsManager is missing.",
            this);
    }

    // cancels pending animation state when the bow is unequipped
    private void OnDisable()
    {
        if (shootingAnimationRoutine != null)
        {
            StopCoroutine(shootingAnimationRoutine);
            shootingAnimationRoutine = null;
        }

        if (animator != null)
        {
            animator.SetBool(IsShootingHash, false);
        }

        hasPendingShot = false;
        IsShooting = false;
        cooldownTimer = 0f;
    }
}
