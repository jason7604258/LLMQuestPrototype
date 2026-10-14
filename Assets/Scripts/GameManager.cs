using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

// keeps the player and shared systems alive while scenes change
[DefaultExecutionOrder(-1000)]
[DisallowMultipleComponent]
public class GameManager : MonoBehaviour
{
    // exposes the active manager without allowing outside replacement
    public static GameManager Instance { get; private set; }

    // adds optional scene roots to the automatic persistent object list
    [Header("Optional Persistent Objects")]
    [Tooltip(
        "Extra root objects that should survive scene changes. " +
        "Stats/EXP, Inventory, HUD, skill UI and QuestSystem are registered automatically.")]
    [SerializeField] private GameObject[] persistentObjects;

    // tracks every root already moved under this persistent manager
    private readonly List<GameObject> registeredObjects = new List<GameObject>();

    // clears old static data when unity starts a new runtime session
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    private static void ResetStaticState()
    {
        Instance = null;
    }

    // creates the manager when a starting scene does not already contain one
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    private static void EnsureInstanceExists()
    {
        if (Instance == null)
        {
            // the generated object uses the same name as the authored manager
            new GameObject("== PERSISTENT OBJECTS ==")
                .AddComponent<GameManager>();
        }

        Instance.RegisterCorePersistentObjects(SceneManager.GetActiveScene());
    }

    // keeps one manager and begins tracking scene changes
    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            // duplicate scene systems are removed without touching the active copy
            CleanUpAndDestroy();
            return;
        }

        Instance = this;
        gameObject.name = "== PERSISTENT OBJECTS ==";
        DontDestroyOnLoad(gameObject);
        SceneManager.sceneLoaded += HandleSceneLoaded;
        MarkPersistentObjects();
    }

    // registers shared systems that belong to the newly loaded scene
    private void HandleSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        RegisterCorePersistentObjects(scene);
    }

    // gathers singleton systems and named ui roots that must survive scene changes
    private void RegisterCorePersistentObjects(Scene scene)
    {
        if (StatsManager.Instance != null)
        {
            RegisterPersistentObject(StatsManager.Instance.gameObject);
        }

        if (Inventory_Manager.Instance != null)
        {
            RegisterPersistentObject(Inventory_Manager.Instance.gameObject);
        }

        if (QuestManager.Instance != null)
        {
            RegisterPersistentObject(QuestManager.Instance.gameObject);
        }

        RegisterNamedSceneRoot(scene, "Player UI");
        RegisterNamedSceneRoot(scene, "ExpCanvas");
        // preserving the ui manager also preserves all skill slot progress
        RegisterNamedSceneRoot(scene, "UIManager");
    }

    // keeps one named scene root or removes it when a persistent copy exists
    private void RegisterNamedSceneRoot(Scene scene, string objectName)
    {
        if (!scene.IsValid() || !scene.isLoaded)
        {
            return;
        }

        foreach (GameObject root in scene.GetRootGameObjects())
        {
            if (root.name != objectName)
            {
                continue;
            }

            GameObject existing = FindPersistentObject(objectName);
            if (existing != null && existing != root)
            {
                // the previous scene copy remains the source of shared state
                Debug.Log(
                    $"Removing duplicate scene object '{objectName}' because " +
                    "the persistent copy is already active.",
                    root);
                Destroy(root);
                return;
            }

            RegisterPersistentObject(root);
            return;
        }
    }

    // registers optional roots assigned through the inspector
    private void MarkPersistentObjects()
    {
        if (persistentObjects == null)
        {
            return;
        }

        foreach (GameObject obj in persistentObjects)
        {
            RegisterPersistentObject(obj);
        }
    }

    // moves one unique root under the manager so unity keeps it between scenes
    public void RegisterPersistentObject(GameObject obj)
    {
        if (obj == null)
        {
            return;
        }

        Transform rootTransform = obj.transform;
        // stop at the highest root outside this manager
        while (rootTransform.parent != null &&
               rootTransform.parent != transform)
        {
            rootTransform = rootTransform.parent;
        }

        GameObject root = rootTransform.gameObject;
        if (root == gameObject || registeredObjects.Contains(root))
        {
            return;
        }

        GameObject existing = FindPersistentObject(root.name);
        if (existing != null && existing != root)
        {
            // matching names identify a duplicate of an already preserved root
            Destroy(root);
            return;
        }

        registeredObjects.Add(root);
        root.transform.SetParent(transform, true);
        Debug.Log($"GameManager is preserving '{root.name}' between scenes.", root);
    }

    // finds a preserved root by name and removes destroyed entries from the list
    public GameObject FindPersistentObject(string objectName)
    {
        registeredObjects.RemoveAll(obj => obj == null);

        foreach (GameObject obj in registeredObjects)
        {
            if (obj.name == objectName)
            {
                return obj;
            }
        }

        return null;
    }

    // disables and removes a second manager with its duplicate scene systems
    private void CleanUpAndDestroy()
    {
        // a scene may contain a configured manager even when one already exists
        if (persistentObjects != null)
        {
            foreach (GameObject obj in persistentObjects)
            {
                if (obj == null)
                {
                    continue;
                }

                GameObject root = obj.transform.root.gameObject;
                if (Instance == null || !Instance.registeredObjects.Contains(root))
                {
                    // disabling first prevents one frame of duplicate input or rendering
                    root.SetActive(false);
                    Destroy(root);
                }
            }
        }

        gameObject.SetActive(false);
        Destroy(gameObject);
    }

    // releases scene callbacks and singleton ownership for the active manager
    private void OnDestroy()
    {
        if (Instance != this)
        {
            return;
        }

        SceneManager.sceneLoaded -= HandleSceneLoaded;
        Instance = null;
    }
}
