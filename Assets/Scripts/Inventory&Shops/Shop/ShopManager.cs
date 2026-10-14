using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

[DisallowMultipleComponent]
// fills shop slots and handles buying selling categories and pause state
public class ShopManager : MonoBehaviour
{
    // shared state lets inventory slots know which shop is open
    public static event Action<ShopManager, bool> OnShopStateChanged;
    public static ShopManager ActiveShop { get; private set; }

    // offers grouped by the three shop category buttons
    [Header("Shop Inventory")]
    [SerializeField] private List<ShopItems> shopItems = new List<ShopItems>();
    [SerializeField] private List<ShopItems> shopWeapons = new List<ShopItems>();
    [SerializeField] private List<ShopItems> shopArmour = new List<ShopItems>();

    // reusable ui slots filled from the selected category
    [Header("Shop UI")]
    [SerializeField] private ShopSlot[] shopSlots;

    // links used for inventory changes and panel visibility
    [Header("References")]
    [SerializeField] private Inventory_Manager inventoryManager;
    [SerializeField] private CanvasGroup shopCanvasGroup;

    // cached category buttons and current shop state
    private Button itemShopButton;
    private Button weaponShopButton;
    private Button armourShopButton;
    private bool isShopOpen;
    private bool ownsPause;
    private float timeScaleBeforeShop = 1f;

    // reports whether this shop currently accepts inventory sales
    public bool IsShopOpen => isShopOpen;

    // finds all scene links needed by this shop
    private void Awake()
    {
        ResolveShopSlots();
        ResolveInventoryManager();
        ResolveShopCanvasGroup();
        ResolveCategoryButtons();
    }

    // connects buttons fills the first category and starts closed
    private void Start()
    {
        BindCategoryButtons();
        OpenItemShop();
        SetShopOpen(false);
    }

    // notices if another ui system changes the shop canvas directly
    private void Update()
    {
        RefreshShopState();
    }

    // removes listeners releases pause and clears shared shop state
    private void OnDisable()
    {
        UnbindCategoryButtons();
        ReleaseShopPause();

        if (ActiveShop == this)
        {
            ActiveShop = null;
            isShopOpen = false;
            OnShopStateChanged?.Invoke(this, false);
        }
    }

    // fills visible slots from one category and hides any extra slots
    public void PopulateShopItems(List<ShopItems> categoryItems)
    {
        ResolveShopSlots();

        int itemCount = categoryItems != null ? categoryItems.Count : 0;

        for (int i = 0; i < shopSlots.Length; i++)
        {
            ShopSlot slot = shopSlots[i];
            if (slot == null)
                continue;

            bool hasValidItem = i < itemCount &&
                                categoryItems[i] != null &&
                                categoryItems[i].itemSO != null;

            if (!hasValidItem)
            {
                // invalid or missing entries leave no clickable empty offer
                slot.gameObject.SetActive(false);
                continue;
            }

            ShopItems shopItem = categoryItems[i];
            slot.Initialize(shopItem.itemSO, shopItem.price, this);
            slot.gameObject.SetActive(true);
        }
    }

    // shows regular item offers
    public void OpenItemShop()
    {
        PopulateShopItems(shopItems);
    }

    // shows weapon offers
    public void OpenWeaponShop()
    {
        PopulateShopItems(shopWeapons);
    }

    // shows armour offers
    public void OpenArmourShop()
    {
        PopulateShopItems(shopArmour);
    }

    // asks the inventory to buy one item at the shown price
    public bool TryBuyItem(ItemSO itemSO, int price)
    {
        ResolveInventoryManager();

        if (inventoryManager == null)
        {
            Debug.LogWarning("Shop cannot complete a purchase because Inventory Manager is missing.", this);
            return false;
        }

        return inventoryManager.TryPurchaseItem(itemSO, 1, Mathf.Max(0, price));
    }

    // sells one inventory item when it appears in any shop category
    public bool TrySellItem(InventorySlot inventorySlot)
    {
        if (!isShopOpen || inventorySlot == null || inventorySlot.IsEmpty)
            return false;

        ResolveInventoryManager();
        if (inventoryManager == null)
        {
            Debug.LogWarning("Shop cannot complete a sale because Inventory Manager is missing.", this);
            return false;
        }

        ItemSO itemSO = inventorySlot.itemSO;
        // use the first matching category price as the sale value
        if (TryGetShopPrice(shopItems, itemSO, out int price) ||
            TryGetShopPrice(shopWeapons, itemSO, out price) ||
            TryGetShopPrice(shopArmour, itemSO, out price))
            return inventoryManager.TrySellItem(inventorySlot, price);

        Debug.Log($"{itemSO.itemName} is not accepted by this shop.", this);
        return false;
    }

    // changes panel visibility and updates pause and shared shop state
    public void SetShopOpen(bool isOpen)
    {
        if (isOpen && !isShopOpen)
            OpenItemShop();

        ResolveShopCanvasGroup();
        if (shopCanvasGroup != null)
        {
            shopCanvasGroup.alpha = isOpen ? 1f : 0f;
            shopCanvasGroup.interactable = isOpen;
            shopCanvasGroup.blocksRaycasts = isOpen;
        }

        SetShopState(isOpen);
    }

    // looks up the price of one item inside a category
    private static bool TryGetShopPrice(
        List<ShopItems> categoryItems,
        ItemSO itemSO,
        out int price)
    {
        if (categoryItems != null)
        {
            foreach (ShopItems shopItem in categoryItems)
            {
                if (shopItem != null && shopItem.itemSO == itemSO)
                {
                    price = Mathf.Max(0, shopItem.price);
                    return true;
                }
            }
        }

        price = 0;
        return false;
    }

    // finds category buttons by their current scene object names
    private void ResolveCategoryButtons()
    {
        Button[] buttons = GetComponentsInChildren<Button>(true);
        foreach (Button button in buttons)
        {
            switch (button.gameObject.name)
            {
                case "ShopButton":
                    itemShopButton = button;
                    break;
                case "ShopButton (1)":
                    weaponShopButton = button;
                    break;
                case "ShopButton (2)":
                    armourShopButton = button;
                    break;
            }
        }
    }

    // connects each category button without duplicate listeners
    private void BindCategoryButtons()
    {
        ResolveCategoryButtons();
        UnbindCategoryButtons();

        if (itemShopButton != null)
            itemShopButton.onClick.AddListener(OpenItemShop);
        if (weaponShopButton != null)
            weaponShopButton.onClick.AddListener(OpenWeaponShop);
        if (armourShopButton != null)
            armourShopButton.onClick.AddListener(OpenArmourShop);
    }

    // removes all category button listeners added by this shop
    private void UnbindCategoryButtons()
    {
        if (itemShopButton != null)
            itemShopButton.onClick.RemoveListener(OpenItemShop);
        if (weaponShopButton != null)
            weaponShopButton.onClick.RemoveListener(OpenWeaponShop);
        if (armourShopButton != null)
            armourShopButton.onClick.RemoveListener(OpenArmourShop);
    }

    // pauses game time while this shop is open
    private void AcquireShopPause()
    {
        if (ownsPause)
            return;

        timeScaleBeforeShop = Time.timeScale;
        Time.timeScale = 0f;
        ownsPause = true;
    }

    // restores the time scale that existed before the shop opened
    private void ReleaseShopPause()
    {
        if (!ownsPause)
            return;

        Time.timeScale = timeScaleBeforeShop;
        ownsPause = false;
    }

    // finds the inventory manager when it is not assigned
    private void ResolveInventoryManager()
    {
        if (inventoryManager == null)
            inventoryManager = FindAnyObjectByType<Inventory_Manager>();
    }

    // finds the canvas group that controls shop visibility
    private void ResolveShopCanvasGroup()
    {
        if (shopCanvasGroup == null)
            shopCanvasGroup = GetComponentInParent<CanvasGroup>();
    }

    // keeps internal state in sync with the actual canvas state
    private void RefreshShopState()
    {
        ResolveShopCanvasGroup();

        bool shouldBeOpen = isActiveAndEnabled &&
                            gameObject.activeInHierarchy &&
                            shopCanvasGroup != null &&
                            shopCanvasGroup.alpha > 0.001f &&
                            shopCanvasGroup.interactable &&
                            shopCanvasGroup.blocksRaycasts;

        if (shouldBeOpen != isShopOpen)
            SetShopState(shouldBeOpen);
    }

    // switches the active shop and owns pause for only one shop at a time
    private void SetShopState(bool isOpen)
    {
        if (isShopOpen == isOpen && ActiveShop == (isOpen ? this : null))
            return;

        if (isOpen)
        {
            // close any previous shop before making this one active
            if (ActiveShop != null && ActiveShop != this)
            {
                ShopManager previousShop = ActiveShop;
                previousShop.isShopOpen = false;
                previousShop.ReleaseShopPause();
                OnShopStateChanged?.Invoke(previousShop, false);
            }

            isShopOpen = true;
            ActiveShop = this;
            AcquireShopPause();
        }
        else
        {
            isShopOpen = false;
            ReleaseShopPause();

            if (ActiveShop == this)
                ActiveShop = null;
        }

        OnShopStateChanged?.Invoke(this, isOpen);
    }

    // refreshes missing shop slot links from child objects
    private void ResolveShopSlots()
    {
        bool needsRefresh = shopSlots == null || shopSlots.Length == 0;

        if (!needsRefresh)
        {
            foreach (ShopSlot slot in shopSlots)
            {
                if (slot == null)
                {
                    needsRefresh = true;
                    break;
                }
            }
        }

        if (needsRefresh)
            shopSlots = GetComponentsInChildren<ShopSlot>(true);

        if (shopSlots == null)
            shopSlots = Array.Empty<ShopSlot>();
    }
}

[Serializable]
// pairs an item with its price inside one shop category
public class ShopItems
{
    // offer data shown in one shop slot
    public ItemSO itemSO;

    [Min(0)]
    public int price;
}
