using UnityEngine;
using TMPro;
using UnityEngine.SceneManagement;

// connects player health changes to the shared stats and health display
public class PlayerHealth : MonoBehaviour
{
    // points to the health label and its update animation
    public TMP_Text healthText;
    public Animator healthTextAnim;

    // stores the shared stats source used for health changes
    private StatsManager stats;

    // binds scene ui and begins listening for stat changes
    private void OnEnable()
    {
        SceneManager.sceneLoaded -= HandleSceneLoaded;
        SceneManager.sceneLoaded += HandleSceneLoaded;
        BindHealthUI(SceneManager.GetActiveScene());

        stats = StatsManager.Instance;
        if (stats != null)
        {
            // removing first prevents two callbacks after this player is enabled again
            stats.StatsChanged -= UpdateHealthText;
            stats.StatsChanged += UpdateHealthText;
        }

        UpdateHealthText();
    }

    // removes callbacks before the player stops running
    private void OnDisable()
    {
        SceneManager.sceneLoaded -= HandleSceneLoaded;

        if (stats != null)
        {
            stats.StatsChanged -= UpdateHealthText;
        }
    }

    // reconnects the health label after a new scene becomes active
    private void HandleSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        BindHealthUI(scene);
        UpdateHealthText();
    }

    // finds the health label from persistent ui or the supplied scene
    private void BindHealthUI(Scene scene)
    {
        GameObject playerUI = GameManager.Instance != null
            ? GameManager.Instance.FindPersistentObject("Player UI")
            : null;

        if (playerUI == null && scene.IsValid() && scene.isLoaded)
        {
            // this fallback supports scenes running without the game manager
            foreach (GameObject root in scene.GetRootGameObjects())
            {
                if (root.name == "Player UI")
                {
                    playerUI = root;
                    break;
                }
            }
        }

        if (playerUI == null)
        {
            return;
        }

        TMP_Text[] labels = playerUI.GetComponentsInChildren<TMP_Text>(true);
        foreach (TMP_Text label in labels)
        {
            // the health label is selected by its authored object name
            if (label != null && label.gameObject.name == "HP Text")
            {
                healthText = label;
                healthTextAnim = label.GetComponent<Animator>();
                return;
            }
        }
    }

    // changes shared health, plays feedback, and disables a defeated player
    public void ChangeHealth(int amount)
    {
        if (stats == null)
        {
            return;
        }

        stats.ChangeHealth(amount);

        if (healthTextAnim != null)
        {
            healthTextAnim.Play("TextUpdate");
        }

        if (stats.currentHealth <= 0)
        {
            gameObject.SetActive(false);
        }
    }

    // copies the current health values into the visible label
    private void UpdateHealthText()
    {
        if (stats != null && healthText != null)
        {
            healthText.text = "HP: " + stats.currentHealth + " / " + stats.maxHealth;
        }
    }
}
