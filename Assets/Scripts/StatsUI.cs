using TMPro;
using UnityEngine;

// opens the stats panel, pauses gameplay, and shows current player values
[DisallowMultipleComponent]
[RequireComponent(typeof(CanvasGroup))]
public class StatsUI : MonoBehaviour
{
    // stores the ordered stat rows, panel visibility control, and input action
    public GameObject[] statsSlots;
    public CanvasGroup statsCanvas;
    public string toggleButton = "ToggleStats";

    // remembers panel state and the time scale that must be restored
    private bool isOpen;
    private float previousTimeScale = 1f;

    // repairs the canvas reference and any hidden zero scale from scene setup
    private void Awake()
    {
        if (statsCanvas == null)
        {
            statsCanvas = GetComponent<CanvasGroup>();
        }

        RectTransform rect = transform as RectTransform;
        if (rect != null && rect.localScale.sqrMagnitude < 0.001f)
        {
            rect.localScale = Vector3.one;
        }
    }

    // begins listening for shared stat changes while the panel can be used
    private void OnEnable()
    {
        if (StatsManager.Instance != null)
        {
            StatsManager.Instance.StatsChanged += UpdateAllStats;
        }
    }

    // draws the first values and starts with the panel closed
    private void Start()
    {
        UpdateAllStats();
        previousTimeScale = Time.timeScale;
        SetStatsOpen(false);
    }

    // listens for the stats panel input once per frame
    private void Update()
    {
        if (Input.GetButtonDown(toggleButton))
        {
            ToggleStats();
        }
    }

    // switches between the current open and closed state
    public void ToggleStats()
    {
        SetStatsOpen(!isOpen);
    }

    // updates panel interaction and pauses or restores gameplay time
    private void SetStatsOpen(bool shouldOpen)
    {
        if (statsCanvas == null)
        {
            return;
        }

        isOpen = shouldOpen;
        statsCanvas.alpha = isOpen ? 1f : 0f;
        statsCanvas.interactable = isOpen;
        statsCanvas.blocksRaycasts = isOpen;

        if (isOpen)
        {
            // save the current scale so another pause system is respected later
            UpdateAllStats();
            previousTimeScale = Time.timeScale;
            Time.timeScale = 0f;
        }
        else
        {
            Time.timeScale = previousTimeScale;
        }
    }

    // refreshes every row from the shared stats manager
    public void UpdateAllStats()
    {
        UpdateDamage();
        UpdateWeaponRange();
        UpdateAttackCooldown();
        UpdateKnockbackForce();
        UpdateKnockbackTime();
        UpdateStunTime();
        UpdateMoveSpeed();
        UpdateHealth();
    }

    // writes the current damage value into its row
    public void UpdateDamage()
    {
        if (StatsManager.Instance != null)
        {
            SetSlotText(0, "Damage: " + StatsManager.Instance.damage);
        }
    }

    // writes the current weapon range into its row
    public void UpdateWeaponRange()
    {
        if (StatsManager.Instance != null)
        {
            SetSlotText(1, "Weapon Range: " + StatsManager.Instance.weaponRange);
        }
    }

    // writes the current attack cooldown into its row
    public void UpdateAttackCooldown()
    {
        if (StatsManager.Instance != null)
        {
            SetSlotText(2, "Attack Cooldown: " + StatsManager.Instance.attackCooldown);
        }
    }

    // writes the current knockback force into its row
    public void UpdateKnockbackForce()
    {
        if (StatsManager.Instance != null)
        {
            SetSlotText(3, "Knockback Force: " + StatsManager.Instance.knockbackForce);
        }
    }

    // writes the current knockback time into its row
    public void UpdateKnockbackTime()
    {
        if (StatsManager.Instance != null)
        {
            SetSlotText(4, "Knockback Time: " + StatsManager.Instance.knockbackTime);
        }
    }

    // writes the current stun time into its row
    public void UpdateStunTime()
    {
        if (StatsManager.Instance != null)
        {
            SetSlotText(5, "Stun Time: " + StatsManager.Instance.stunTime);
        }
    }

    // writes the current movement speed into its row
    public void UpdateMoveSpeed()
    {
        if (StatsManager.Instance != null)
        {
            SetSlotText(6, "Move Speed: " + StatsManager.Instance.moveSpeed);
        }
    }

    // writes current and maximum health into the final row
    public void UpdateHealth()
    {
        if (StatsManager.Instance != null)
        {
            SetSlotText(
                7,
                "Health: " +
                StatsManager.Instance.currentHealth +
                " / " +
                StatsManager.Instance.maxHealth);
        }
    }

    // safely finds the text child for one ordered row
    private void SetSlotText(int index, string value)
    {
        if (statsSlots == null || index < 0 || index >= statsSlots.Length ||
            statsSlots[index] == null)
        {
            return;
        }

        TMP_Text text = statsSlots[index].GetComponentInChildren<TMP_Text>();
        if (text != null)
        {
            text.text = value;
        }
    }

    // removes callbacks and restores time if the panel closes unexpectedly
    private void OnDisable()
    {
        if (StatsManager.Instance != null)
        {
            StatsManager.Instance.StatsChanged -= UpdateAllStats;
        }

        if (isOpen)
        {
            Time.timeScale = previousTimeScale;
            isOpen = false;
        }
    }
}
