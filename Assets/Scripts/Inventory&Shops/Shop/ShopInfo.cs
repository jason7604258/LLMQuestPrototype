using System.Collections.Generic;
using TMPro;
using UnityEngine;

[DisallowMultipleComponent]
[RequireComponent(typeof(CanvasGroup))]
// shows item details beside the cursor while a shop slot is hovered
public class ShopInfo : MonoBehaviour
{
    // panel visibility and cursor spacing
    [Header("Panel")]
    [SerializeField] private CanvasGroup infoPanel;
    [SerializeField] private Vector2 cursorOffset = new Vector2(20f, -20f);

    // labels filled from the hovered item
    [Header("Text")]
    [SerializeField] private TMP_Text itemNameText;
    [SerializeField] private TMP_Text itemDescriptionText;
    [SerializeField] private TMP_Text[] statTexts;

    // cached panel shape and current visibility
    private RectTransform infoPanelRect;
    private bool isVisible;

    // finds ui links and starts with the panel hidden
    private void Awake()
    {
        ResolveReferences();
        HideItemInfo();
    }

    // follows the mouse after normal ui layout work is complete
    private void LateUpdate()
    {
        if (isVisible)
            FollowMouse();
    }

    // fills and shows the panel for one item
    public void ShowItemInfo(ItemSO itemSO)
    {
        if (itemSO == null)
        {
            HideItemInfo();
            return;
        }

        ResolveReferences();

        if (itemNameText != null)
            itemNameText.text = itemSO.itemName;

        if (itemDescriptionText != null)
            itemDescriptionText.text = itemSO.itemDescription;

        RefreshStatTexts(itemSO);
        SetVisible(true);
        FollowMouse();
    }

    // hides the panel and clears all old item text
    public void HideItemInfo()
    {
        ResolveReferences();
        SetVisible(false);

        if (itemNameText != null)
            itemNameText.text = string.Empty;

        if (itemDescriptionText != null)
            itemDescriptionText.text = string.Empty;

        if (statTexts == null)
            return;

        foreach (TMP_Text statText in statTexts)
        {
            if (statText != null)
                statText.text = string.Empty;
        }
    }

    // moves the panel beside the cursor while keeping it on screen
    private void FollowMouse()
    {
        if (infoPanelRect == null)
            return;

        Vector2 desiredPosition = (Vector2)Input.mousePosition + cursorOffset;
        Vector2 panelSize = Vector2.Scale(infoPanelRect.rect.size, infoPanelRect.lossyScale);
        Vector2 pivot = infoPanelRect.pivot;

        // clamp each edge using the panel size and pivot
        desiredPosition.x = Mathf.Clamp(
            desiredPosition.x,
            panelSize.x * pivot.x,
            Screen.width - panelSize.x * (1f - pivot.x));

        desiredPosition.y = Mathf.Clamp(
            desiredPosition.y,
            panelSize.y * pivot.y,
            Screen.height - panelSize.y * (1f - pivot.y));

        infoPanelRect.position = desiredPosition;
    }

    // builds a short list of effects for the available stat labels
    private void RefreshStatTexts(ItemSO itemSO)
    {
        if (statTexts == null || statTexts.Length == 0)
            return;

        List<string> stats = new List<string>();

        if (itemSO.healthRestore > 0)
            stats.Add($"Health +{itemSO.healthRestore}");

        if (itemSO.maxHealthBonus > 0)
            stats.Add($"Max Health +{itemSO.maxHealthBonus}");

        if (itemSO.speedBonus > 0)
            stats.Add($"Speed +{itemSO.speedBonus}");

        if (itemSO.damageBonus > 0)
            stats.Add($"Damage +{itemSO.damageBonus}");

        if (itemSO.duration > 0f)
            stats.Add($"Duration: {itemSO.duration:0.#}s");

        stats.Add($"Stack limit: {Mathf.Max(1, itemSO.stackSize)}");

        // hide unused labels so old values cannot remain visible
        for (int i = 0; i < statTexts.Length; i++)
        {
            TMP_Text statText = statTexts[i];
            if (statText == null)
                continue;

            bool hasStat = i < stats.Count;
            statText.text = hasStat ? stats[i] : string.Empty;
            statText.gameObject.SetActive(hasStat);
        }
    }

    // changes visibility without letting this hover panel block clicks
    private void SetVisible(bool visible)
    {
        isVisible = visible;

        if (infoPanel == null)
            return;

        infoPanel.alpha = visible ? 1f : 0f;
        infoPanel.interactable = false;
        infoPanel.blocksRaycasts = false;
    }

    // finds panel and text links from the expected ui layout
    private void ResolveReferences()
    {
        if (infoPanel == null)
            infoPanel = GetComponent<CanvasGroup>();

        if (infoPanelRect == null)
            infoPanelRect = GetComponent<RectTransform>();

        if (itemNameText == null)
            itemNameText = FindText("NameBacking/Name", "NameBacking/ItemName");

        if (itemDescriptionText == null)
            itemDescriptionText = FindText("Description/DescriptionText");

        if (statTexts == null || statTexts.Length == 0)
        {
            Transform statsRoot = transform.Find("Stats");
            if (statsRoot != null)
                statTexts = statsRoot.GetComponentsInChildren<TMP_Text>(true);
        }
    }

    // returns the first text component found at the given child paths
    private TMP_Text FindText(params string[] paths)
    {
        foreach (string path in paths)
        {
            Transform child = transform.Find(path);
            if (child != null && child.TryGetComponent(out TMP_Text text))
                return text;
        }

        return null;
    }

    // refreshes editor links after inspector changes
    private void OnValidate()
    {
        ResolveReferences();
    }
}
