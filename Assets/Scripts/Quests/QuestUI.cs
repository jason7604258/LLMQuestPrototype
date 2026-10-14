using TMPro;
using UnityEngine;
using UnityEngine.UI;

// prevents two quest ui builders on the same gameobject
[DisallowMultipleComponent]
// creates and updates the quest panel shown during play
public class QuestUI : MonoBehaviour
{
    // fixed panel values keep the panel aligned with the level display
    private const float PanelWidth = 410f;
    private const float MinimumPanelHeight = 430f;
    private static readonly Vector2 LevelAlignedPanelOffset =
        new Vector2(0f, -300f);

    // quest manager that supplies state text and button actions
    [SerializeField] private QuestManager questManager;

    [Header("Layout")]
    // sizes and positions for the open and closed panel
    [SerializeField] private Vector2 panelSize = new Vector2(410f, 430f);
    [SerializeField] private Vector2 panelOffset = new Vector2(0f, -300f);
    [SerializeField] private Vector2 compactPanelSize = new Vector2(410f, 140f);
    [SerializeField] private Vector2 compactPanelOffset = new Vector2(0f, -300f);

    // ui objects created at runtime and reused for later updates
    private RectTransform panelBorder;
    private RectTransform panel;
    private TMP_Text heading;
    private TMP_Text title;
    private TMP_Text introduction;
    private TMP_Text objective;
    private TMP_Text progress;
    private TMP_Text completion;
    private Button startButton;
    private Button detailsButton;
    private TMP_Text detailsButtonLabel;
    // remembers whether full quest details are visible
    private bool isExpanded;

    // shared colors for the panel text and buttons
    private static readonly Color PanelColor =
        new Color(0.055f, 0.047f, 0.075f, 0.94f);
    private static readonly Color BorderColor =
        new Color(0.72f, 0.48f, 0.18f, 1f);
    private static readonly Color PrimaryTextColor =
        new Color(0.96f, 0.88f, 0.68f, 1f);
    private static readonly Color SecondaryTextColor =
        new Color(0.9f, 0.9f, 0.92f, 1f);
    private static readonly Color ButtonColor =
        new Color(0.42f, 0.19f, 0.08f, 1f);

    // checks setup and builds the panel before it is used
    private void Awake()
    {
        // keeps saved layout values within the supported size and position
        panelSize.x = PanelWidth;
        panelSize.y = Mathf.Max(panelSize.y, MinimumPanelHeight);
        compactPanelSize.x = PanelWidth;
        compactPanelSize.y = Mathf.Max(compactPanelSize.y, 140f);
        panelOffset = LevelAlignedPanelOffset;
        compactPanelOffset = LevelAlignedPanelOffset;

        // looks for a quest manager on this gameobject when none was assigned
        if (questManager == null)
        {
            questManager = GetComponent<QuestManager>();
        }

        // disables this component when no quest manager can be found
        if (questManager == null)
        {
            Debug.LogError(
                "QuestUI requires a QuestManager reference.",
                this);
            enabled = false;
            return;
        }

        BuildUI();
    }

    // listens for quest state changes while this ui is active
    private void OnEnable()
    {
        if (questManager != null)
        {
            questManager.QuestStateChanged -= HandleQuestStateChanged;
            questManager.QuestStateChanged += HandleQuestStateChanged;
        }
    }

    // stops listening when this ui is disabled
    private void OnDisable()
    {
        if (questManager != null)
        {
            questManager.QuestStateChanged -= HandleQuestStateChanged;
        }
    }

    // creates every part of the quest panel and connects its buttons
    private void BuildUI()
    {
        // creates the canvas and main panel first
        Canvas canvas = CreateCanvas();
        panel = CreatePanel(canvas.transform);

        heading = CreateText(
            panel,
            "Header",
            "SCENARIO",
            16f,
            FontStyles.Bold,
            TextAlignmentOptions.Left,
            PrimaryTextColor);
        SetRect(heading.rectTransform, 22f, 18f, -22f, 28f);

        title = CreateText(
            panel,
            "TitleText",
            "No active scenario",
            25f,
            FontStyles.Bold,
            TextAlignmentOptions.Left,
            PrimaryTextColor);
        ConfigureAutoSizing(title, 20f, 25f);
        SetRect(title.rectTransform, 22f, 52f, -22f, 36f);

        introduction = CreateText(
            panel,
            "IntroductionText",
            "Preparing the automatic scenario loop.",
            17f,
            FontStyles.Normal,
            TextAlignmentOptions.TopLeft,
            SecondaryTextColor);
        introduction.textWrappingMode = TextWrappingModes.Normal;
        ConfigureAutoSizing(introduction, 14f, 17f);
        SetRect(introduction.rectTransform, 22f, 98f, -22f, 122f);

        objective = CreateText(
            panel,
            "ObjectiveText",
            "Objective: —",
            18f,
            FontStyles.Bold,
            TextAlignmentOptions.Left,
            PrimaryTextColor);
        objective.textWrappingMode = TextWrappingModes.Normal;
        ConfigureAutoSizing(objective, 14f, 18f);
        SetRect(objective.rectTransform, 22f, 232f, -105f, 54f);

        progress = CreateText(
            panel,
            "ProgressText",
            "0 / 5",
            20f,
            FontStyles.Bold,
            TextAlignmentOptions.Right,
            PrimaryTextColor);
        ConfigureAutoSizing(progress, 16f, 20f);
        SetRect(progress.rectTransform, 315f, 232f, -22f, 54f);

        completion = CreateText(
            panel,
            "CompletionText",
            string.Empty,
            16f,
            FontStyles.Italic,
            TextAlignmentOptions.TopLeft,
            new Color(0.66f, 0.92f, 0.63f, 1f));
        completion.textWrappingMode = TextWrappingModes.Normal;
        ConfigureAutoSizing(completion, 13f, 16f);
        SetRect(completion.rectTransform, 22f, 298f, -22f, 62f);

        startButton = CreateButton(panel);
        startButton.onClick.AddListener(questManager.StartScenario);
        TMP_Text startButtonLabel = startButton.GetComponentInChildren<TMP_Text>();

        detailsButton = CreateDetailsButton(panel);
        detailsButton.onClick.AddListener(ToggleDetails);
        detailsButtonLabel = detailsButton.GetComponentInChildren<TMP_Text>();

        // gives the created text and button objects to the quest manager
        questManager.BindUI(
            title,
            introduction,
            objective,
            progress,
            completion,
            startButton,
            startButtonLabel);

        // starts with the small panel until a quest needs more space
        ApplyLayout(false);
    }

    // creates an overlay canvas that scales with screen size
    private Canvas CreateCanvas()
    {
        GameObject canvasObject = new GameObject(
            "QuestCanvas",
            typeof(RectTransform),
            typeof(Canvas),
            typeof(CanvasScaler),
            typeof(GraphicRaycaster));
        canvasObject.transform.SetParent(transform, false);

        // keeps the quest panel above normal scene graphics
        Canvas canvas = canvasObject.GetComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 50;

        // scales from the reference size on different screen shapes
        CanvasScaler scaler = canvasObject.GetComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920f, 1080f);
        scaler.screenMatchMode =
            CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
        scaler.matchWidthOrHeight = 0.5f;

        return canvas;
    }

    // creates the colored border and inner panel
    private RectTransform CreatePanel(Transform parent)
    {
        // border is the anchored outer rectangle
        GameObject borderObject = new GameObject(
            "QuestPanelBorder",
            typeof(RectTransform),
            typeof(Image));
        borderObject.transform.SetParent(parent, false);

        panelBorder = borderObject.GetComponent<RectTransform>();
        panelBorder.anchorMin = Vector2.one;
        panelBorder.anchorMax = Vector2.one;
        panelBorder.pivot = Vector2.one;
        panelBorder.sizeDelta = panelSize + new Vector2(4f, 4f);
        panelBorder.anchoredPosition = panelOffset + new Vector2(2f, -2f);
        Image borderImage = borderObject.GetComponent<Image>();
        borderImage.color = BorderColor;
        borderImage.raycastTarget = false;

        // inner panel fills the border with a small gap
        GameObject panelObject = new GameObject(
            "QuestPanel",
            typeof(RectTransform),
            typeof(Image));
        panelObject.transform.SetParent(panelBorder, false);

        RectTransform panelRect = panelObject.GetComponent<RectTransform>();
        panelRect.anchorMin = Vector2.zero;
        panelRect.anchorMax = Vector2.one;
        panelRect.offsetMin = new Vector2(2f, 2f);
        panelRect.offsetMax = new Vector2(-2f, -2f);
        Image panelImage = panelObject.GetComponent<Image>();
        panelImage.color = PanelColor;
        panelImage.raycastTarget = false;

        return panelRect;
    }

    // creates one text label with shared basic settings
    private static TMP_Text CreateText(
        Transform parent,
        string objectName,
        string initialText,
        float fontSize,
        FontStyles fontStyle,
        TextAlignmentOptions alignment,
        Color color)
    {
        GameObject textObject = new GameObject(
            objectName,
            typeof(RectTransform),
            typeof(TextMeshProUGUI));
        textObject.transform.SetParent(parent, false);

        TMP_Text text = textObject.GetComponent<TMP_Text>();
        text.text = initialText;
        text.fontSize = fontSize;
        text.fontStyle = fontStyle;
        text.alignment = alignment;
        text.color = color;
        text.raycastTarget = false;
        text.overflowMode = TextOverflowModes.Ellipsis;

        return text;
    }

    // creates the wide start next or retry button
    private static Button CreateButton(Transform parent)
    {
        GameObject buttonObject = new GameObject(
            "StartScenarioButton",
            typeof(RectTransform),
            typeof(Image),
            typeof(Button));
        buttonObject.transform.SetParent(parent, false);

        RectTransform buttonRect =
            buttonObject.GetComponent<RectTransform>();
        SetRect(buttonRect, 22f, 370f, -22f, 42f);

        Image buttonImage = buttonObject.GetComponent<Image>();
        buttonImage.color = ButtonColor;

        // sets normal hover and pressed colors
        Button button = buttonObject.GetComponent<Button>();
        ColorBlock colors = button.colors;
        colors.normalColor = ButtonColor;
        colors.highlightedColor =
            new Color(0.58f, 0.29f, 0.11f, 1f);
        colors.pressedColor =
            new Color(0.3f, 0.12f, 0.05f, 1f);
        button.colors = colors;

        // stretches the label across the whole button
        TMP_Text label = CreateText(
            buttonObject.transform,
            "Label",
            "START SCENARIO",
            18f,
            FontStyles.Bold,
            TextAlignmentOptions.Center,
            PrimaryTextColor);
        label.rectTransform.anchorMin = Vector2.zero;
        label.rectTransform.anchorMax = Vector2.one;
        label.rectTransform.offsetMin = Vector2.zero;
        label.rectTransform.offsetMax = Vector2.zero;

        return button;
    }

    // creates the small button that opens or closes quest details
    private static Button CreateDetailsButton(Transform parent)
    {
        GameObject buttonObject = new GameObject(
            "QuestDetailsButton",
            typeof(RectTransform),
            typeof(Image),
            typeof(Button));
        buttonObject.transform.SetParent(parent, false);

        RectTransform buttonRect = buttonObject.GetComponent<RectTransform>();
        buttonRect.anchorMin = Vector2.one;
        buttonRect.anchorMax = Vector2.one;
        buttonRect.pivot = Vector2.one;
        buttonRect.sizeDelta = new Vector2(34f, 30f);
        buttonRect.anchoredPosition = new Vector2(-12f, -12f);

        Image buttonImage = buttonObject.GetComponent<Image>();
        buttonImage.color = ButtonColor;

        // sets normal hover and pressed colors
        Button button = buttonObject.GetComponent<Button>();
        ColorBlock colors = button.colors;
        colors.normalColor = ButtonColor;
        colors.highlightedColor = new Color(0.58f, 0.29f, 0.11f, 1f);
        colors.pressedColor = new Color(0.3f, 0.12f, 0.05f, 1f);
        button.colors = colors;

        // stretches the plus or minus label across the button
        TMP_Text label = CreateText(
            buttonObject.transform,
            "Label",
            "-",
            22f,
            FontStyles.Bold,
            TextAlignmentOptions.Center,
            PrimaryTextColor);
        label.rectTransform.anchorMin = Vector2.zero;
        label.rectTransform.anchorMax = Vector2.one;
        label.rectTransform.offsetMin = Vector2.zero;
        label.rectTransform.offsetMax = Vector2.zero;

        return button;
    }

    // changes panel size when an active quest can show details
    private void ToggleDetails()
    {
        // ignores clicks while there is no stable active quest to display
        if (questManager == null ||
            !questManager.IsQuestActive ||
            questManager.IsNarrativeRequestInProgress)
        {
            return;
        }

        ApplyLayout(!isExpanded);
    }

    // chooses a panel size after any important quest state change
    private void HandleQuestStateChanged()
    {
        if (questManager == null)
        {
            return;
        }

        // opens the panel for loading active completed or failed states
        if (questManager.IsNarrativeRequestInProgress ||
            questManager.IsQuestActive ||
            questManager.IsQuestCompleted ||
            questManager.IsNarrativeGenerationFailed)
        {
            ApplyLayout(true);
        }
        else
        {
            ApplyLayout(false);
        }
    }

    // applies size position visibility and text placement for one panel state
    private void ApplyLayout(bool shouldExpand)
    {
        // waits until required runtime ui objects are ready
        if (panelBorder == null || panel == null || questManager == null)
        {
            return;
        }

        isExpanded = shouldExpand;

        // changes the outer panel size and keeps its border visible
        Vector2 targetSize = isExpanded ? panelSize : compactPanelSize;
        panelBorder.sizeDelta = targetSize + new Vector2(4f, 4f);

        panelBorder.anchorMin = new Vector2(0f, 1f);
        panelBorder.anchorMax = new Vector2(0f, 1f);
        panelBorder.pivot = new Vector2(0f, 1f);
        panelBorder.anchoredPosition = isExpanded
            ? panelOffset
            : compactPanelOffset;

        // decides which controls and text belong in the current state
        bool isActive = questManager.IsQuestActive;
        bool showDetailsToggle =
            isActive && !questManager.IsNarrativeRequestInProgress;
        bool showScenarioButton = questManager.ShouldShowScenarioButton;

        heading.gameObject.SetActive(isExpanded);
        introduction.gameObject.SetActive(isExpanded);
        completion.gameObject.SetActive(isExpanded);
        objective.gameObject.SetActive(isExpanded || isActive);
        progress.gameObject.SetActive(isExpanded || isActive);
        startButton.gameObject.SetActive(showScenarioButton);
        detailsButton.gameObject.SetActive(showDetailsToggle);

        // minus closes details and plus opens them
        if (detailsButtonLabel != null)
        {
            detailsButtonLabel.text = isExpanded ? "-" : "+";
        }

        // places labels for the full panel
        if (isExpanded)
        {
            SetRect(heading.rectTransform, 22f, 18f, -60f, 28f);
            SetRect(title.rectTransform, 22f, 52f, -22f, 36f);
            SetRect(introduction.rectTransform, 22f, 98f, -22f, 122f);
            SetRect(objective.rectTransform, 22f, 232f, -105f, 54f);
            SetRect(progress.rectTransform, 315f, 232f, -22f, 54f);
            SetRect(completion.rectTransform, 22f, 298f, -22f, 62f);
            SetRect(startButton.GetComponent<RectTransform>(), 22f, 370f, -22f, 42f);
        }
        // keeps title objective and progress in the small active panel
        else if (isActive)
        {
            SetRect(title.rectTransform, 18f, 14f, -58f, 34f);
            SetRect(objective.rectTransform, 18f, 58f, -105f, 54f);
            SetRect(progress.rectTransform, 315f, 58f, -18f, 54f);
        }
        // keeps only title and start button in the small idle panel
        else
        {
            SetRect(title.rectTransform, 18f, 14f, -18f, 36f);
            SetRect(startButton.GetComponent<RectTransform>(), 18f, 72f, -18f, 42f);
        }
    }

    // lets a label reduce its font size when text is too long
    private static void ConfigureAutoSizing(
        TMP_Text text,
        float minimumFontSize,
        float maximumFontSize)
    {
        text.enableAutoSizing = true;
        text.fontSizeMin = minimumFontSize;
        text.fontSizeMax = maximumFontSize;
    }

    // places one ui rectangle using distances from the panel edges
    private static void SetRect(
        RectTransform rect,
        float left,
        float top,
        float right,
        float height)
    {
        rect.anchorMin = new Vector2(0f, 1f);
        rect.anchorMax = new Vector2(1f, 1f);
        rect.pivot = new Vector2(0.5f, 1f);
        rect.offsetMin = new Vector2(left, -top - height);
        rect.offsetMax = new Vector2(right, -top);
    }
}
