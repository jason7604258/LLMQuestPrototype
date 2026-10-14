using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

[DisallowMultipleComponent]
[RequireComponent(typeof(Button))]
// displays one shop offer and forwards buy or hover actions
public class ShopSlot : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
{
    // item and price offered by this slot
    [Header("Item")]
    [SerializeField] private ItemSO itemSO;
    [SerializeField, Min(0)] private int price;

    // ui elements used to display this offer
    [Header("UI References")]
    [SerializeField] private TMP_Text itemNameText;
    [SerializeField] private TMP_Text priceText;
    [SerializeField] private Image itemImage;

    // cached shop systems used by clicks and hover details
    private ShopManager shopManager;
    private ShopInfo shopInfo;

    // finds scene links and draws the starting offer
    private void Awake()
    {
        ResolveUIReferences();
        ResolveShopManager();
        ResolveShopInfo();
        RefreshUI();
    }

    // fills this slot with one offer from its shop category
    public void Initialize(ItemSO newItemSO, int newPrice, ShopManager owner = null)
    {
        itemSO = newItemSO;
        price = Mathf.Max(0, newPrice);
        shopManager = owner;
        ResolveUIReferences();
        ResolveShopManager();
        ResolveShopInfo();
        RefreshUI();
    }

    // asks the owning shop to buy the displayed item
    public void OnBuyButtonClicked()
    {
        if (itemSO == null)
            return;

        ResolveShopManager();
        if (shopManager == null)
        {
            Debug.LogWarning($"{name} cannot buy an item because Shop Manager is missing.", this);
            return;
        }

        shopManager.TryBuyItem(itemSO, price);
    }

    // shows item details when the pointer enters this slot
    public void OnPointerEnter(PointerEventData eventData)
    {
        if (itemSO == null)
            return;

        ResolveShopInfo();
        if (shopInfo != null)
            shopInfo.ShowItemInfo(itemSO);
    }

    // hides item details when the pointer leaves this slot
    public void OnPointerExit(PointerEventData eventData)
    {
        if (shopInfo != null)
            shopInfo.HideItemInfo();
    }

    // makes sure hover details close with an inactive slot
    private void OnDisable()
    {
        if (shopInfo != null)
            shopInfo.HideItemInfo();
    }

    // updates the offer icon name and price
    private void RefreshUI()
    {
        bool hasItem = itemSO != null;

        if (itemImage != null)
        {
            itemImage.sprite = hasItem ? itemSO.icon : null;
            itemImage.preserveAspect = true;
            itemImage.enabled = hasItem;
        }

        if (itemNameText != null)
            itemNameText.text = hasItem ? itemSO.itemName : string.Empty;

        if (priceText != null)
            priceText.text = hasItem ? price.ToString() : string.Empty;
    }

    // finds ui elements from the expected slot layout
    private void ResolveUIReferences()
    {
        if (itemNameText == null)
        {
            Transform itemName = transform.Find("NameBanner/ItemName");
            if (itemName != null)
                itemNameText = itemName.GetComponent<TMP_Text>();
        }

        if (priceText == null)
        {
            Transform priceLabel = transform.Find("Cost/Price");
            if (priceLabel != null)
                priceText = priceLabel.GetComponent<TMP_Text>();
        }

        if (itemImage == null)
        {
            Transform icon = transform.Find("ItemIcon");
            if (icon != null)
                itemImage = icon.GetComponent<Image>();
        }
    }

    // finds the shop that owns this slot
    private void ResolveShopManager()
    {
        if (shopManager == null)
            shopManager = GetComponentInParent<ShopManager>();
    }

    // finds the hover panel inside the owning shop
    private void ResolveShopInfo()
    {
        ResolveShopManager();
        if (shopInfo == null && shopManager != null)
            shopInfo = shopManager.GetComponentInChildren<ShopInfo>(true);
    }

    // keeps the price valid and refreshes editor previews
    private void OnValidate()
    {
        price = Mathf.Max(0, price);
        ResolveUIReferences();
        RefreshUI();
    }
}
