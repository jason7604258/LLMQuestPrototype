using UnityEngine;

// lists the broad ways an item is used by the game
public enum ItemType
{
    Gold,
    HealthPotion,
    StatBoost,
    Material
}

[CreateAssetMenu(
    fileName = "New Item",
    menuName = "Items/Item")]
// stores reusable item data shared by loot inventory and shops
public class ItemSO : ScriptableObject
{
    // stable id and text shown for this item
    [Header("Basic Information")]
    [SerializeField] private string itemId;
    public string itemName;

    [TextArea]
    public string itemDescription;

    public Sprite icon;
    public ItemType itemType;

    // maximum amount allowed in one inventory slot
    [Header("Inventory")]
    [Min(1)]
    [Tooltip("The maximum quantity of this item that one inventory slot can hold. Gold does not use inventory slots.")]
    public int stackSize = 5;

    // stat changes applied when the player uses this item
    [Header("Effects")]
    [Min(0)]
    public int healthRestore;

    [Min(0)]
    public int maxHealthBonus;

    [Min(0)]
    public int speedBonus;

    [Min(0)]
    public int damageBonus;

    // optional time before stat bonuses are removed
    [Header("Temporary Effect")]
    [Min(0f)]
    [Tooltip("0 keeps stat bonuses permanently. A value above 0 removes Max Health, Damage, and Speed bonuses after this many seconds. Health restore is always instant.")]
    public float duration;

    // quest systems use this id instead of the display name
    public string ItemId => itemId;

    // cleans values after changes in the inspector
    private void OnValidate()
    {
        itemId = itemId?.Trim();
        itemName = itemName?.Trim();
        stackSize = Mathf.Max(1, stackSize);
    }
}
