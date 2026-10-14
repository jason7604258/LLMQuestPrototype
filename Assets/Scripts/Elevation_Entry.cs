using UnityEngine;

// changes collision and drawing order when the player enters raised ground
public class Elevation_Entry : MonoBehaviour
{
    // blocks the lower side of the mountain until the player enters
    public Collider2D[] mountainColliders;

    // keeps the player inside the raised area after entering
    public Collider2D[] boundaryColliders;

    // opens the mountain path and draws the player above the mountain
    private void OnTriggerEnter2D(Collider2D collision)
    {
        if (collision.gameObject.tag == "Player")
        {
            foreach (Collider2D mountain in mountainColliders)
            {
                // entering removes the lower mountain barrier
                mountain.enabled = false;
            }

            foreach (Collider2D boundary in boundaryColliders)
            {
                // raised area boundaries become active while the player is inside
                boundary.enabled = true;
            }

            collision.gameObject.GetComponent<SpriteRenderer>().sortingOrder = 15;
        }
    }
}
