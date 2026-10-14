using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

[DisallowMultipleComponent]
// stores one item stack and handles clicks on its inventory slot
public class InventorySlot : MonoBehaviour, IPointerClickHandler
{
    // item data held by this slot
    [Header("Item Data")]
    public ItemSO itemSO;

    [Min(0)]
    public int quantity;

    // ui elements that show the item and its quantity
    [Header("UI References")]
    public Image itemImage;
    public TMP_Text quantityText;

    // true when this slot has no usable item stack
    public bool IsEmpty => itemSO == null || quantity <= 0;

    // cached systems used when the player clicks this slot
    private Inventory_Manager inventoryManager;
    private static ShopManager activeShop;

    // finds the owning inventory and draws the starting state
    private void Awake()
    {
        inventoryManager = GetComponentInParent<Inventory_Manager>();
        UpdateUI();
    }

    // listens for shop changes while this slot is active
    private void OnEnable()
    {
        ShopManager.OnShopStateChanged -= HandleShopStateChanged;
        ShopManager.OnShopStateChanged += HandleShopStateChanged;
        activeShop = ShopManager.ActiveShop;
    }

    // stops listening when this slot is inactive
    private void OnDisable()
    {
        ShopManager.OnShopStateChanged -= HandleShopStateChanged;
    }

    // keeps the shared active shop reference in sync
    private void HandleShopStateChanged(ShopManager shopManager, bool isOpen)
    {
        if (isOpen)
        {
            activeShop = shopManager;
        }
        else if (activeShop == shopManager)
        {
            activeShop = null;
        }
    }

    // sells or uses with left click, drops with right click
    public void OnPointerClick(PointerEventData eventData)
    {
        if (IsEmpty)
            return;

        if (inventoryManager == null)
        {
            inventoryManager = GetComponentInParent<Inventory_Manager>();
        }

        if (inventoryManager == null)
        {
            Debug.LogWarning($"{name} cannot use its item because Inventory Manager is missing.", this);
            return;
        }

        if (eventData.button == PointerEventData.InputButton.Left)
        {
            // an open shop changes left click from use to sell
            if (activeShop != null)
                activeShop.TrySellItem(this);
            else
                inventoryManager.UseItem(this);
        }
        else if (eventData.button == PointerEventData.InputButton.Right)
        {
            inventoryManager.DropItem(this);
        }
    }

    // checks whether this slot holds the given item
    public bool Contains(ItemSO item)
    {
        return !IsEmpty && itemSO == item;
    }

    // replaces this stack and clears invalid values
    public void SetItem(ItemSO item, int amount)
    {
        if (item == null || amount <= 0)
        {
            Clear();
            return;
        }

        itemSO = item;
        quantity = amount;
        UpdateUI();
    }

    // changes the stack size and keeps it inside the integer range
    public void AddQuantity(int amount)
    {
        if (IsEmpty || amount == 0)
            return;

        long updatedQuantity = (long)quantity + amount;
        quantity = updatedQuantity <= 0
            ? 0
            : updatedQuantity > int.MaxValue
                ? int.MaxValue
                : (int)updatedQuantity;

        if (quantity == 0)
            itemSO = null;

        UpdateUI();
    }

    // removes all item data from this slot
    public void Clear()
    {
        itemSO = null;
        quantity = 0;
        UpdateUI();
    }

    // updates the icon and quantity shown to the player
    public void UpdateUI()
    {
        bool hasItem = !IsEmpty;

        if (itemImage != null)
        {
            itemImage.sprite = hasItem ? itemSO.icon : null;
            itemImage.preserveAspect = true;
            itemImage.gameObject.SetActive(hasItem);
        }

        if (quantityText != null)
            quantityText.text = hasItem ? quantity.ToString() : string.Empty;
    }
}
