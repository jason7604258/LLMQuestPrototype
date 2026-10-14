using UnityEngine;

// switches the player between melee and bow controls and visuals
[DisallowMultipleComponent]
[RequireComponent(typeof(Player_Combat), typeof(Player_bow))]
public class Player_ChangeEquipment : MonoBehaviour
{
    // lists the two equipment styles the player can use
    public enum EquipmentMode
    {
        Melee,
        Bow
    }

    // names the input action used to swap equipment
    [Header("Input")]
    [SerializeField] private string changeEquipmentButton = "ChangeEquipment";

    // selects the equipment enabled when play begins
    [Header("Starting Mode")]
    [SerializeField] private EquipmentMode startingMode = EquipmentMode.Bow;

    // connects both combat scripts and the shared player animator
    [Header("References")]
    [SerializeField] private Player_Combat playerCombat;
    [SerializeField] private Player_bow playerBow;
    [SerializeField] private Animator animator;

    // exposes the selected mode without allowing outside direct changes
    public EquipmentMode CurrentMode { get; private set; }

    // stores the optional animator layer used for bow visuals
    private int archerLayerIndex = -1;

    // fills common references when the component is added or reset in the inspector
    private void Reset()
    {
        playerCombat = GetComponent<Player_Combat>();
        playerBow = GetComponent<Player_bow>();
        animator = GetComponent<Animator>();
    }

    // repairs missing references and applies the configured starting mode
    private void Awake()
    {
        if (playerCombat == null)
        {
            playerCombat = GetComponent<Player_Combat>();
        }

        if (playerBow == null)
        {
            playerBow = GetComponent<Player_bow>();
        }

        if (animator == null)
        {
            animator = GetComponent<Animator>();
        }

        if (animator != null)
        {
            archerLayerIndex = animator.GetLayerIndex("ArcherLayer");
        }

        SetMode(startingMode);
    }

    // listens for the equipment swap input while gameplay time is running
    private void Update()
    {
        if (Time.timeScale > 0f && Input.GetButtonDown(changeEquipmentButton))
        {
            ToggleEquipment();
        }
    }

    // changes to the other available equipment mode
    public void ToggleEquipment()
    {
        SetMode(CurrentMode == EquipmentMode.Bow
            ? EquipmentMode.Melee
            : EquipmentMode.Bow);
    }

    // enables one attack script and matches the animator layer to it
    public void SetMode(EquipmentMode mode)
    {
        CurrentMode = mode;
        bool bowEquipped = mode == EquipmentMode.Bow;

        if (playerCombat != null)
        {
            playerCombat.enabled = !bowEquipped;
        }

        if (playerBow != null)
        {
            playerBow.enabled = bowEquipped;
        }

        // the archer layer only replaces visuals while the bow is equipped
        if (animator != null && archerLayerIndex >= 0)
        {
            animator.SetLayerWeight(archerLayerIndex, bowEquipped ? 1f : 0f);
        }
    }
}
