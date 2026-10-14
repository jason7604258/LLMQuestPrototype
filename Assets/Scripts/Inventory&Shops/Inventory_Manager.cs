using System;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;

[DefaultExecutionOrder(-80)]
[DisallowMultipleComponent]
// owns item stacks currency item use and world drops
public class Inventory_Manager : MonoBehaviour
{
    // shared access and quest progress event
    public static Inventory_Manager Instance { get; private set; }
    public static event Action<string, int> ItemCollected;

    // slots that hold regular items
    [Header("Item Slots")]
    [SerializeField] private InventorySlot[] itemSlots;

    // helper that applies item effects to player stats
    [Header("Item Use")]
    [SerializeField] private UseItem useItem;

    // settings used when the player drops one item
    [Header("Manual Drop")]
    [SerializeField] private Loot lootPrefab;
    [SerializeField] private Transform dropOrigin;
    [SerializeField] private Vector2 dropOffset = new Vector2(0.75f, 0f);
    [SerializeField, Min(0f)] private float droppedLootPickupDelay = 0.5f;

    // currency value and its ui label
    [Header("Currency")]
    [SerializeField, Min(0)] private int gold;
    [SerializeField] private TMP_Text goldText;

    // keeps one inventory instance and prepares its links and ui
    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            // remove duplicate managers before they can subscribe to events
            enabled = false;
            Destroy(gameObject);
            return;
        }

        Instance = this;
        ResolveUseItem();
        ResolveDropOrigin();
        TryFindGoldText();
        ResolveItemSlots();
        RefreshAllSlots();
        RefreshGoldUI();
    }

    // reconnects events and scene links when this manager becomes active
    private void OnEnable()
    {
        if (Instance != this)
        {
            return;
        }

        // remove old listeners first so enabling twice cannot add duplicates
        Loot.PickupRequested -= TryCollectLoot;
        Loot.PickupRequested += TryCollectLoot;
        SceneManager.sceneLoaded -= HandleSceneLoaded;
        SceneManager.sceneLoaded += HandleSceneLoaded;
        ResolveUseItem();
        ResolveDropOrigin();
        ResolveItemSlots();
        RefreshAllSlots();
        RefreshGoldUI();
    }

    // removes event listeners while this manager is inactive
    private void OnDisable()
    {
        Loot.PickupRequested -= TryCollectLoot;
        SceneManager.sceneLoaded -= HandleSceneLoaded;
    }

    // refreshes the drop origin and inventory ui after a scene loads
    private void HandleSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        dropOrigin = null;
        ResolveDropOrigin();
        RefreshAllSlots();
        RefreshGoldUI();
    }

    // accepts a full loot stack and then reports valid quest progress
    private void TryCollectLoot(Loot loot)
    {
        if (loot != null && !loot.IsCollected && TryAddItem(loot.Item, loot.Quantity))
        {
            string collectedItemId = loot.Item.ItemId;
            int collectedQuantity = loot.Quantity;
            loot.ConfirmCollection();

            // runtime drops do not count and authored loot needs a stable id
            if (loot.CountsForQuestProgress && !string.IsNullOrWhiteSpace(collectedItemId))
            {
                ItemCollected?.Invoke(collectedItemId, collectedQuantity);
            }
            else if (loot.CountsForQuestProgress)
            {
                Debug.LogWarning(
                    $"Collected item '{loot.Item.name}' has no stable item ID; " +
                    "quest progress was not reported.",
                    loot.Item);
            }
        }
    }

    // checks whether the complete quantity can fit without changing any slots
    public bool CanAddItem(ItemSO itemSO, int quantity)
    {
        if (itemSO == null || quantity <= 0)
            return false;

        // currency is stored separately and never uses an item slot
        if (itemSO.itemType == ItemType.Gold)
            return true;

        ResolveItemSlots();

        int stackSize = Mathf.Max(1, itemSO.stackSize);
        long availableSpace = 0;

        foreach (InventorySlot slot in itemSlots)
        {
            if (slot == null)
                continue;

            if (slot.Contains(itemSO))
            {
                availableSpace += Mathf.Max(0, stackSize - slot.quantity);
            }
            else if (slot.IsEmpty)
            {
                availableSpace += stackSize;
            }

            if (availableSpace >= quantity)
                return true;
        }

        return false;
    }

    // adds a complete item quantity or leaves the inventory unchanged
    public bool TryAddItem(ItemSO itemSO, int quantity)
    {
        if (itemSO == null)
        {
            Debug.LogWarning("Inventory ignored loot because its ItemSO is missing.", this);
            return false;
        }

        if (quantity <= 0)
        {
            Debug.LogWarning($"Inventory ignored {itemSO.name} because its quantity is {quantity}.", this);
            return false;
        }

        if (itemSO.itemType == ItemType.Gold)
        {
            // loot quantity already holds the final gold value from the world
            long updatedGold = (long)gold + quantity;
            gold = updatedGold > int.MaxValue ? int.MaxValue : (int)updatedGold;
            RefreshGoldUI();
            return true;
        }

        if (!CanAddItem(itemSO, quantity))
        {
            Debug.Log($"Inventory has no room for the complete pickup: {quantity} x {itemSO.itemName}.", this);
            return false;
        }

        int remaining = quantity;
        int stackSize = Mathf.Max(1, itemSO.stackSize);

        // fill existing stacks before using new slots
        foreach (InventorySlot slot in itemSlots)
        {
            if (slot == null || !slot.Contains(itemSO) || slot.quantity >= stackSize)
                continue;

            int amountToAdd = Mathf.Min(stackSize - slot.quantity, remaining);
            slot.AddQuantity(amountToAdd);
            remaining -= amountToAdd;

            if (remaining <= 0)
                return true;
        }

        // put the remaining items into empty slots without passing the stack limit
        foreach (InventorySlot slot in itemSlots)
        {
            if (slot != null && slot.IsEmpty)
            {
                int amountToAdd = Mathf.Min(stackSize, remaining);
                slot.SetItem(itemSO, amountToAdd);
                remaining -= amountToAdd;

                if (remaining <= 0)
                    return true;
            }
        }

        // reaching this point means another system changed the slots during this call
        Debug.LogError($"Inventory capacity changed while adding {itemSO.itemName}.", this);
        return false;
    }

    // checks a shop purchase before adding the item and spending gold
    public bool TryPurchaseItem(ItemSO itemSO, int quantity, int price)
    {
        if (itemSO == null || quantity <= 0 || price < 0)
        {
            Debug.LogWarning("Inventory rejected an invalid shop purchase.", this);
            return false;
        }

        if (itemSO.itemType == ItemType.Gold)
        {
            Debug.LogWarning("Gold cannot be purchased as a regular shop item.", this);
            return false;
        }

        if (gold < price)
        {
            Debug.Log($"Not enough gold to buy {itemSO.itemName}. Need {price}, have {gold}.", this);
            return false;
        }

        if (!CanAddItem(itemSO, quantity))
        {
            Debug.Log($"Inventory has no room for {quantity} x {itemSO.itemName}.", this);
            return false;
        }

        // add first so a failed add never takes the player gold
        if (!TryAddItem(itemSO, quantity))
            return false;

        gold -= price;
        RefreshGoldUI();
        return true;
    }

    // removes one item from a known slot and pays its sale value
    public bool TrySellItem(InventorySlot slot, int salePrice)
    {
        if (slot == null || slot.IsEmpty || salePrice < 0)
            return false;

        ResolveItemSlots();
        if (System.Array.IndexOf(itemSlots, slot) < 0)
        {
            Debug.LogWarning("Inventory rejected a sale from an unknown slot.", this);
            return false;
        }

        if (slot.itemSO.itemType == ItemType.Gold)
        {
            Debug.LogWarning("Gold cannot be sold as a regular inventory item.", this);
            return false;
        }

        ItemSO soldItem = slot.itemSO;
        slot.AddQuantity(-1);

        long updatedGold = (long)gold + salePrice;
        gold = updatedGold > int.MaxValue ? int.MaxValue : (int)updatedGold;
        RefreshGoldUI();

        Debug.Log($"Sold 1 x {soldItem.itemName} for {salePrice} gold.", this);
        return true;
    }

    // applies one item and only consumes it when an effect succeeds
    public bool UseItem(InventorySlot slot)
    {
        if (slot == null || slot.IsEmpty)
        {
            return false;
        }

        ItemSO itemSO = slot.itemSO;
        if (itemSO.itemType == ItemType.Gold)
        {
            Debug.LogWarning("Gold is currency and cannot be used from an inventory slot.", this);
            return false;
        }

        ResolveUseItem();
        if (useItem == null || !useItem.TryApplyItemEffects(itemSO))
        {
            Debug.LogWarning($"{itemSO.itemName} has no applicable item effects.", itemSO);
            return false;
        }

        slot.AddQuantity(-1);
        return true;
    }

    // creates one loot object beside the player and removes one item
    public bool DropItem(InventorySlot slot)
    {
        if (slot == null || slot.IsEmpty)
            return false;

        if (lootPrefab == null)
        {
            Debug.LogWarning("Cannot drop item because Loot Prefab is not assigned.", this);
            return false;
        }

        ResolveDropOrigin();
        if (dropOrigin == null)
        {
            Debug.LogWarning("Cannot drop item because a Player/drop origin could not be found.", this);
            return false;
        }

        ItemSO itemSO = slot.itemSO;
        Vector3 spawnPosition = dropOrigin.position + (Vector3)dropOffset;
        Loot droppedLoot = Instantiate(lootPrefab, spawnPosition, Quaternion.identity);

        droppedLoot.Initialize(itemSO, 1, droppedLootPickupDelay);
        slot.AddQuantity(-1);
        return true;
    }

    // finds or creates the small helper that applies item effects
    private void ResolveUseItem()
    {
        if (useItem == null)
        {
            useItem = GetComponent<UseItem>();
        }

        if (useItem == null && Application.isPlaying)
        {
            useItem = gameObject.AddComponent<UseItem>();
        }
    }

    // uses the tagged player as the default world drop position
    private void ResolveDropOrigin()
    {
        if (dropOrigin != null)
            return;

        GameObject player = GameObject.FindGameObjectWithTag("Player");
        if (player != null)
            dropOrigin = player.transform;
    }

    // refreshes missing slot links from the inventory children
    private void ResolveItemSlots()
    {
        bool needsRefresh = itemSlots == null || itemSlots.Length == 0;

        if (!needsRefresh)
        {
            foreach (InventorySlot slot in itemSlots)
            {
                if (slot == null)
                {
                    needsRefresh = true;
                    break;
                }
            }
        }

        if (needsRefresh)
            itemSlots = GetComponentsInChildren<InventorySlot>(true);

        if (itemSlots == null)
            itemSlots = System.Array.Empty<InventorySlot>();
    }

    // redraws every valid inventory slot
    private void RefreshAllSlots()
    {
        foreach (InventorySlot slot in itemSlots)
        {
            if (slot != null)
                slot.UpdateUI();
        }
    }

    // finds the default gold label when it was not assigned
    private void TryFindGoldText()
    {
        if (goldText != null)
            return;

        Transform amountText = transform.Find("Gold/AmountText");
        if (amountText != null)
            goldText = amountText.GetComponent<TMP_Text>();

        if (goldText == null)
            Debug.LogWarning("Inventory Manager could not find Gold/AmountText.", this);
    }

    // writes the current gold amount to the ui
    private void RefreshGoldUI()
    {
        if (goldText != null)
            goldText.text = gold.ToString();
    }

    // keeps inspector values inside their valid ranges
    private void OnValidate()
    {
        gold = Mathf.Max(0, gold);
        droppedLootPickupDelay = Mathf.Max(0f, droppedLootPickupDelay);
    }

    // clears shared state when the active inventory is destroyed
    private void OnDestroy()
    {
        if (Instance == this)
        {
            SceneManager.sceneLoaded -= HandleSceneLoaded;
            Instance = null;
        }
    }
}
