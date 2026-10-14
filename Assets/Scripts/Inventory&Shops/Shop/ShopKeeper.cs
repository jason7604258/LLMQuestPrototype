using UnityEngine;
using UnityEngine.InputSystem;

[DisallowMultipleComponent]
[RequireComponent(typeof(Animator), typeof(CircleCollider2D))]
// opens the nearby shop when the player uses the interact action
public class ShopKeeper : MonoBehaviour
{
    // names shared with the animator and input action asset
    private const string PlayerInRangeParameter = "PlayerInRange";
    private const string InteractActionName = "Player/Interact";

    // scene links for the prompt and shop window
    [SerializeField] private Animator interactionPromptAnimator;
    [SerializeField] private ShopManager shopManager;

    // current player range state used by interaction checks
    public bool PlayerInRange { get; private set; }

    // cached input action used while this component is active
    private InputAction interactAction;

    // prepares the range trigger and required links
    private void Awake()
    {
        CircleCollider2D rangeTrigger = GetComponent<CircleCollider2D>();
        if (rangeTrigger != null)
            rangeTrigger.isTrigger = true;

        ResolveShopManager();
        ResolveInteractAction();
        SetPlayerInRange(false);
    }

    // starts listening for the interact action
    private void OnEnable()
    {
        ResolveInteractAction();

        if (interactAction != null)
            interactAction.performed += HandleInteract;
    }

    // stops input and closes the shop when this keeper is inactive
    private void OnDisable()
    {
        if (interactAction != null)
            interactAction.performed -= HandleInteract;

        CloseShop();
        SetPlayerInRange(false);
    }

    // shows the interaction prompt when the player enters range
    private void OnTriggerEnter2D(Collider2D collision)
    {
        if (collision.CompareTag("Player"))
            SetPlayerInRange(true);
    }

    // closes the shop and hides the prompt when the player leaves
    private void OnTriggerExit2D(Collider2D collision)
    {
        if (collision.CompareTag("Player"))
        {
            CloseShop();
            SetPlayerInRange(false);
        }
    }

    // toggles the shop only while the player is in range
    private void HandleInteract(InputAction.CallbackContext context)
    {
        if (!PlayerInRange)
            return;

        ResolveShopManager();
        if (shopManager == null)
        {
            Debug.LogWarning("ShopKeeper could not find a ShopManager.", this);
            return;
        }

        shopManager.SetShopOpen(!shopManager.IsShopOpen);
    }

    // finds the shared interact action from the input system
    private void ResolveInteractAction()
    {
        if (interactAction == null && InputSystem.actions != null)
            interactAction = InputSystem.actions.FindAction(InteractActionName);
    }

    // finds the shop manager when it is not assigned
    private void ResolveShopManager()
    {
        if (shopManager == null)
            shopManager = FindAnyObjectByType<ShopManager>();
    }

    // safely closes the linked shop
    private void CloseShop()
    {
        ResolveShopManager();

        if (shopManager != null && shopManager.IsShopOpen)
            shopManager.SetShopOpen(false);
    }

    // stores range state and updates the interaction prompt
    private void SetPlayerInRange(bool isInRange)
    {
        PlayerInRange = isInRange;

        if (interactionPromptAnimator != null)
            interactionPromptAnimator.SetBool(PlayerInRangeParameter, isInRange);
    }
}
