using System;
using System.Collections;
using UnityEngine;

[DisallowMultipleComponent]
[RequireComponent(typeof(Collider2D))]
// represents an item pickup placed or dropped in the world
public class Loot : MonoBehaviour
{
    // item and quantity given to the inventory
    [Header("Item")]
    [SerializeField] private ItemSO itemSO;

    [Min(1)]
    [Tooltip("The exact number of items (or gold) added to the inventory when collected.")]
    [SerializeField] private int quantity = 1;

    [Tooltip("Only authored world pickups should advance CollectItems scenarios. Runtime drops default to false.")]
    [SerializeField] private bool countsForQuestProgress = true;

    // visuals and timing used during collection
    [Header("Presentation")]
    [SerializeField] private SpriteRenderer spriteRenderer;
    [SerializeField] private Animator animator;

    [Min(0f)]
    [SerializeField] private float pickupDuration = 0.35f;

    // cached animation state used for a fast lookup
    private static readonly int LootPickupState = Animator.StringToHash("Loot_Pickup");

    // cached parts and current pickup state
    private Collider2D pickupCollider;
    private bool isCollected;
    private bool isPickupPending;
    private Coroutine pickupDelayRoutine;

    // asks the inventory to accept this full pickup
    public static event Action<Loot> PickupRequested;

    // read only values used by the inventory and quest systems
    public ItemSO Item => itemSO;
    public int Quantity => quantity;
    public bool IsCollected => isCollected;
    public bool CountsForQuestProgress => countsForQuestProgress;

    // finds required parts and fixes the starting quantity
    private void Awake()
    {
        CacheComponents();
        quantity = Mathf.Max(1, quantity);
    }

    // prepares loot created by dropping an inventory item
    public void Initialize(
        ItemSO newItemSO,
        int newQuantity,
        float pickupDelay = 0f,
        bool shouldCountForQuestProgress = false)
    {
        if (newItemSO == null)
        {
            Debug.LogError("Loot cannot be initialized without an ItemSO.", this);
            return;
        }

        CacheComponents();
        itemSO = newItemSO;
        quantity = Mathf.Max(1, newQuantity);
        countsForQuestProgress = shouldCountForQuestProgress;
        isCollected = false;
        isPickupPending = false;
        UpdateAppearance();

        // a short delay stops the player from picking up a fresh drop at once
        if (pickupDelayRoutine != null)
            StopCoroutine(pickupDelayRoutine);

        if (pickupDelay > 0f)
            pickupDelayRoutine = StartCoroutine(DelayPickup(pickupDelay));
        else if (pickupCollider != null)
            pickupCollider.enabled = true;
    }

    // keeps inspector values valid and refreshes the preview
    private void OnValidate()
    {
        CacheComponents();
        quantity = Mathf.Max(1, quantity);
        pickupDuration = Mathf.Max(0f, pickupDuration);

        if (pickupCollider != null)
        {
            pickupCollider.isTrigger = true;
        }

        if (itemSO == null)
        {
            return;
        }

        UpdateAppearance();
    }

    // asks the inventory to collect this loot when the player enters
    private void OnTriggerEnter2D(Collider2D other)
    {
        if (isCollected || isPickupPending || !other.CompareTag("Player"))
        {
            return;
        }

        if (itemSO == null)
        {
            Debug.LogWarning($"{name} cannot be collected because Item SO is not assigned.", this);
            return;
        }

        isPickupPending = true;

        // the inventory accepts the full quantity or leaves this loot in the world
        PickupRequested?.Invoke(this);

        // a failed request may be tried again after inventory space is cleared
        if (!isCollected)
        {
            isPickupPending = false;
        }
    }

    // locks collection and starts the pickup presentation
    public void ConfirmCollection()
    {
        if (isCollected)
            return;

        isCollected = true;
        isPickupPending = false;

        if (pickupCollider != null)
        {
            pickupCollider.enabled = false;
        }

        StartCoroutine(PlayPickupAndDestroy());
    }

    // disables pickup until the dropped item's delay ends
    private IEnumerator DelayPickup(float delay)
    {
        if (pickupCollider != null)
            pickupCollider.enabled = false;

        yield return new WaitForSecondsRealtime(delay);

        if (!isCollected && pickupCollider != null)
            pickupCollider.enabled = true;

        pickupDelayRoutine = null;
    }

    // copies the item icon and name onto this world object
    private void UpdateAppearance()
    {
        if (itemSO == null)
            return;

        if (spriteRenderer != null)
            spriteRenderer.sprite = itemSO.icon;

        gameObject.name = $"Loot - {itemSO.itemName}";
    }

    // plays the authored animation or a simple fade before removal
    private IEnumerator PlayPickupAndDestroy()
    {
        bool hasPickupAnimation = animator != null &&
                                  animator.runtimeAnimatorController != null &&
                                  animator.HasState(0, LootPickupState);

        if (hasPickupAnimation)
        {
            // use the animator when its pickup state is available
            animator.Play(LootPickupState, 0, 0f);

            if (pickupDuration > 0f)
            {
                yield return new WaitForSeconds(pickupDuration);
            }

            Destroy(gameObject);
            yield break;
        }

        if (pickupDuration <= 0f)
        {
            Destroy(gameObject);
            yield break;
        }

        Vector3 startScale = transform.localScale;
        Color startColor = spriteRenderer != null ? spriteRenderer.color : Color.white;
        float elapsed = 0f;

        while (elapsed < pickupDuration)
        {
            elapsed += Time.deltaTime;
            float progress = Mathf.Clamp01(elapsed / pickupDuration);

            // shrink and fade when no pickup animation is available
            transform.localScale = Vector3.Lerp(startScale, startScale * 0.35f, progress);

            if (spriteRenderer != null)
            {
                Color color = startColor;
                color.a = Mathf.Lerp(startColor.a, 0f, progress);
                spriteRenderer.color = color;
            }

            yield return null;
        }

        Destroy(gameObject);
    }

    // finds the collider renderer and animator when they are not assigned
    private void CacheComponents()
    {
        if (pickupCollider == null)
        {
            pickupCollider = GetComponent<Collider2D>();
        }

        if (spriteRenderer == null)
        {
            spriteRenderer = GetComponentInChildren<SpriteRenderer>();
        }

        if (animator == null)
        {
            animator = GetComponent<Animator>();
        }
    }
}
