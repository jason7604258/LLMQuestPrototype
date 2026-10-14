using Unity.Cinemachine;
using UnityEngine;
using UnityEngine.SceneManagement;

// reconnects the persistent camera rig after each scene loads
// each scene keeps its own confiner collider
[DisallowMultipleComponent]
public class ConfinerFinder : MonoBehaviour
{
    // names the scene object that limits camera movement
    [SerializeField] private string confinerObjectName = "Confiner";

    // listens for scene changes and also binds the current scene immediately
    private void OnEnable()
    {
        SceneManager.sceneLoaded -= HandleSceneLoaded;
        SceneManager.sceneLoaded += HandleSceneLoaded;
        Rebind(SceneManager.GetActiveScene());
    }

    // removes the scene callback when this component is disabled
    private void OnDisable()
    {
        SceneManager.sceneLoaded -= HandleSceneLoaded;
    }

    // binds the camera rig to objects from the newly loaded scene
    private void HandleSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        Rebind(scene);
    }

    // updates every cinemachine camera with the active player and confiner
    private void Rebind(Scene scene)
    {
        if (!scene.IsValid() || !scene.isLoaded)
        {
            return;
        }

        Transform player = FindChildRecursive(transform.root, "Player");
        Collider2D confinerShape = FindSceneCollider(scene, confinerObjectName);

        // a missing player keeps the current target, while the confiner still updates
        foreach (CinemachineCamera camera in GetComponentsInChildren<CinemachineCamera>(true))
        {
            if (player != null)
            {
                camera.Target.TrackingTarget = player;
            }

            CinemachineConfiner2D confiner = camera.GetComponent<CinemachineConfiner2D>();
            if (confiner == null)
            {
                continue;
            }

            confiner.BoundingShape2D = confinerShape;
            confiner.InvalidateBoundingShapeCache();
            camera.PreviousStateIsValid = false;
        }

        if (confinerShape == null)
        {
            Debug.LogWarning(
                $"Scene '{scene.name}' has no '{confinerObjectName}' Collider2D; " +
                "the persistent camera will not use a Cinemachine confiner in this scene.",
                this);
        }
    }

    // finds the named collider anywhere under a root in the supplied scene
    private static Collider2D FindSceneCollider(Scene scene, string objectName)
    {
        foreach (GameObject root in scene.GetRootGameObjects())
        {
            Transform match = root.name == objectName
                ? root.transform
                : FindChildRecursive(root.transform, objectName);

            if (match != null && match.TryGetComponent(out Collider2D collider))
            {
                return collider;
            }
        }

        return null;
    }

    // searches all children until an object with the requested name is found
    private static Transform FindChildRecursive(Transform parent, string objectName)
    {
        foreach (Transform child in parent)
        {
            if (child.name == objectName)
            {
                return child;
            }

            Transform nested = FindChildRecursive(child, objectName);
            if (nested != null)
            {
                return nested;
            }
        }

        return null;
    }
}
