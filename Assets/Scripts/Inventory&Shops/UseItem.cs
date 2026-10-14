using System.Collections;
using UnityEngine;

[DisallowMultipleComponent]
// sends item effects to the player stats system
public class UseItem : MonoBehaviour
{
    // applies instant effects and starts removal for temporary bonuses
    public bool TryApplyItemEffects(ItemSO itemSO)
    {
        if (itemSO == null)
        {
            return false;
        }

        StatsManager stats = StatsManager.Instance;
        if (stats == null)
        {
            Debug.LogWarning($"Cannot apply {itemSO.itemName}: Stats Manager is missing.", this);
            return false;
        }

        bool applied = stats.TryApplyItemEffects(itemSO);
        bool hasTemporaryStats = itemSO.duration > 0f &&
                                 (itemSO.maxHealthBonus > 0 ||
                                  itemSO.speedBonus > 0 ||
                                  itemSO.damageBonus > 0);

        // only stat bonuses need to be removed after the timer
        if (applied && hasTemporaryStats)
        {
            StartCoroutine(RemoveEffectsAfterDelay(
                stats,
                itemSO.duration,
                itemSO.maxHealthBonus,
                itemSO.damageBonus,
                itemSO.speedBonus));
        }

        return applied;
    }

    // waits for the item duration before removing its stat bonuses
    private static IEnumerator RemoveEffectsAfterDelay(
        StatsManager stats,
        float duration,
        int maxHealthBonus,
        int damageBonus,
        int speedBonus)
    {
        yield return new WaitForSeconds(duration);

        // the stats object may be gone after a scene change
        if (stats != null)
        {
            stats.RemoveTemporaryItemEffects(maxHealthBonus, damageBonus, speedBonus);
        }
    }
}
