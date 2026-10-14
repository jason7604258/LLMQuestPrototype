using System.Collections;
using Unity.Cinemachine;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

// sends the player to another scene through one shared fade transition
public class SceneChanger : MonoBehaviour
{
    // selects the destination scene and player arrival position
    [Header("Destination")]
    [SerializeField] private string sceneToLoad;
    [SerializeField] private Vector2 newPlayerPosition;

    // controls how quickly the screen fades to and from black
    [Header("Fade")]
    [SerializeField, Min(0.05f)] private float fadeDuration = 0.5f;

    // prevents this entrance from starting more than one transition
    private bool hasTriggered;

    // starts a transition when the player enters this trigger
    private void OnTriggerEnter2D(Collider2D other)
    {
        if (hasTriggered || !other.CompareTag("Player"))
        {
            return;
        }

        BeginTransition();
    }

    // validates and starts a transition from a trigger or ui button
    public void BeginTransition()
    {
        if (hasTriggered || SceneTransitionManager.IsTransitioning)
        {
            return;
        }

        if (string.IsNullOrWhiteSpace(sceneToLoad))
        {
            // an empty destination cannot produce a safe scene change
            Debug.LogError("SceneChanger has no destination scene assigned.", this);
            return;
        }

        if (!Application.CanStreamedLevelBeLoaded(sceneToLoad))
        {
            Debug.LogError(
                $"Scene '{sceneToLoad}' cannot be loaded. Add it to File > Build Profiles > Scene List.",
                this);
            return;
        }

        hasTriggered = true;
        Transform player = GameManager.Instance != null
            ? GameManager.Instance.FindPersistentObject("Player")?.transform
            : null;

        if (player == null)
        {
            // this fallback supports scenes running without the game manager
            GameObject playerObject = GameObject.FindGameObjectWithTag("Player");
            player = playerObject != null ? playerObject.transform : null;
        }

        SceneTransitionManager.LoadScene(
            sceneToLoad,
            newPlayerPosition,
            player,
            fadeDuration);
    }
}

// creates one persistent fade overlay and coordinates every scene load
internal sealed class SceneTransitionManager : MonoBehaviour
{
    // keeps the fade above normal ui and stores the one active manager
    private const int FadeCanvasSortOrder = 32760;
    private static SceneTransitionManager instance;

    // stores the fade controls and the currently running transition
    private CanvasGroup fadeCanvasGroup;
    private Coroutine transitionRoutine;

    // lets entrances reject input while another scene is loading
    public static bool IsTransitioning { get; private set; }

    // prepares the fade overlay before the first scene appears
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    private static void CreateBeforeFirstScene()
    {
        EnsureInstance();
    }

    // returns the existing manager or creates and prepares a new one
    private static SceneTransitionManager EnsureInstance()
    {
        if (instance != null)
        {
            return instance;
        }

        GameObject root = new GameObject(
            "SceneTransitionManager",
            typeof(RectTransform),
            typeof(Canvas),
            typeof(CanvasScaler),
            typeof(CanvasGroup));
        instance = root.AddComponent<SceneTransitionManager>();
        DontDestroyOnLoad(root);
        instance.BuildFadeCanvas();
        return instance;
    }

    // keeps one manager and repairs its fade canvas when needed
    private void Awake()
    {
        if (instance != null && instance != this)
        {
            Destroy(gameObject);
            return;
        }

        instance = this;
        DontDestroyOnLoad(gameObject);

        if (fadeCanvasGroup == null)
        {
            BuildFadeCanvas();
        }
    }

    // reveals the first scene because starting play is not a transition
    private void Start()
    {
        fadeCanvasGroup.alpha = 0f;
        IsTransitioning = false;
        SetInputBlocked(false);
    }

    // starts one shared load routine with a safe minimum fade time
    public static void LoadScene(
        string sceneName,
        Vector2 newPlayerPosition,
        Transform player,
        float fadeDuration)
    {
        SceneTransitionManager manager = EnsureInstance();

        if (IsTransitioning)
        {
            return;
        }

        if (manager.transitionRoutine != null)
        {
            // only a leftover local routine can reach this point
            manager.StopCoroutine(manager.transitionRoutine);
        }

        manager.transitionRoutine = manager.StartCoroutine(
            manager.LoadSceneRoutine(
                sceneName,
                newPlayerPosition,
                player,
                Mathf.Max(0.05f, fadeDuration)));
    }

    // builds or repairs a full screen black overlay on this object
    private void BuildFadeCanvas()
    {
        Canvas canvas = gameObject.GetComponent<Canvas>();
        if (canvas == null)
        {
            canvas = gameObject.AddComponent<Canvas>();
        }

        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.overrideSorting = true;
        canvas.sortingOrder = FadeCanvasSortOrder;

        CanvasScaler scaler = gameObject.GetComponent<CanvasScaler>();
        if (scaler == null)
        {
            scaler = gameObject.AddComponent<CanvasScaler>();
        }

        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920f, 1080f);
        scaler.matchWidthOrHeight = 0.5f;

        fadeCanvasGroup = gameObject.GetComponent<CanvasGroup>();
        if (fadeCanvasGroup == null)
        {
            fadeCanvasGroup = gameObject.AddComponent<CanvasGroup>();
        }

        Transform existingOverlay = transform.Find("FadeToBlack");
        // reuse an existing child when the manager was authored in a scene
        GameObject overlay = existingOverlay != null
            ? existingOverlay.gameObject
            : new GameObject("FadeToBlack", typeof(RectTransform), typeof(CanvasRenderer), typeof(Image));

        overlay.transform.SetParent(transform, false);

        RectTransform overlayRect = overlay.GetComponent<RectTransform>();
        overlayRect.anchorMin = Vector2.zero;
        overlayRect.anchorMax = Vector2.one;
        overlayRect.offsetMin = Vector2.zero;
        overlayRect.offsetMax = Vector2.zero;

        Image overlayImage = overlay.GetComponent<Image>();
        overlayImage.color = Color.black;
        overlayImage.raycastTarget = true;

        fadeCanvasGroup.alpha = 1f;
        SetInputBlocked(true);
    }

    // fades out, moves the player, loads the destination, and fades back in
    private IEnumerator LoadSceneRoutine(
        string sceneName,
        Vector2 newPlayerPosition,
        Transform player,
        float fadeDuration)
    {
        IsTransitioning = true;
        SetInputBlocked(true);

        yield return FadeTo(1f, fadeDuration);

        // move the persistent player only while the screen is fully black
        MovePlayer(newPlayerPosition, player);

        AsyncOperation loadOperation = SceneManager.LoadSceneAsync(sceneName);
        if (loadOperation == null)
        {
            // failed loading returns control without leaving the screen covered
            Debug.LogError($"Unity could not begin loading scene '{sceneName}'.");
            yield return FadeTo(0f, fadeDuration);
            IsTransitioning = false;
            SetInputBlocked(false);
            transitionRoutine = null;
            yield break;
        }

        while (!loadOperation.isDone)
        {
            yield return null;
        }

        // keep one full destination frame hidden before beginning the reveal
        fadeCanvasGroup.alpha = 1f;
        Canvas.ForceUpdateCanvases();
        yield return null;

        yield return FadeTo(0f, fadeDuration);

        IsTransitioning = false;
        SetInputBlocked(false);
        transitionRoutine = null;
    }

    // moves the player through physics and resets camera smoothing after the teleport
    private static void MovePlayer(Vector2 destination, Transform player)
    {
        if (player == null)
        {
            Debug.LogError("The destination scene loaded, but the persistent Player could not be found.");
            return;
        }

        Vector3 previousPosition = player.position;

        if (player.TryGetComponent(out Rigidbody2D body))
        {
            // moving through the rigidbody keeps its physics state in sync
            body.linearVelocity = Vector2.zero;
            body.angularVelocity = 0f;
            body.position = destination;
        }
        else
        {
            player.position = destination;
        }

        Physics2D.SyncTransforms();

        // tell cinemachine this movement was an instant teleport
        // resetting its old state also removes the previous scene confiner result
        Vector3 positionDelta = player.position - previousPosition;
        GameObject persistentRoot = GameManager.Instance != null
            ? GameManager.Instance.gameObject
            : player.transform.root.gameObject;

        foreach (CinemachineCamera camera in
                 persistentRoot.GetComponentsInChildren<CinemachineCamera>(true))
        {
            camera.OnTargetObjectWarped(player, positionDelta);
            camera.PreviousStateIsValid = false;
        }
    }

    // eases the overlay toward one alpha using time that continues while paused
    private IEnumerator FadeTo(float targetAlpha, float duration)
    {
        float startAlpha = fadeCanvasGroup.alpha;
        float elapsed = 0f;

        if (targetAlpha > startAlpha)
        {
            SetInputBlocked(true);
        }

        while (elapsed < duration)
        {
            // limiting one step prevents scene loading time from skipping the fade
            elapsed += Mathf.Min(Time.unscaledDeltaTime, 0.05f);
            float progress = Mathf.Clamp01(elapsed / duration);
            float easedProgress = Mathf.SmoothStep(0f, 1f, progress);
            fadeCanvasGroup.alpha = Mathf.Lerp(startAlpha, targetAlpha, easedProgress);
            Canvas.ForceUpdateCanvases();
            yield return null;
        }

        fadeCanvasGroup.alpha = targetAlpha;
        Canvas.ForceUpdateCanvases();

        if (Mathf.Approximately(targetAlpha, 0f) && !IsTransitioning)
        {
            SetInputBlocked(false);
        }
    }

    // makes the fade overlay accept or ignore pointer input
    private void SetInputBlocked(bool blocked)
    {
        fadeCanvasGroup.blocksRaycasts = blocked;
        fadeCanvasGroup.interactable = blocked;
    }
}
