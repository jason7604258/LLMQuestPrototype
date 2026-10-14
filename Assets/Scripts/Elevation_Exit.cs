using UnityEngine;

// restores collision and drawing order when the player leaves raised ground
public class Elevation_Exit : MonoBehaviour
{
    // blocks the lower side of the mountain after the player leaves
    public Collider2D[] mountainColliders;

    // keeps the player inside the raised area until reaching this exit
    public Collider2D[] boundaryColliders;

    // closes the mountain path and draws the player below the mountain
    private void OnTriggerEnter2D(Collider2D collision)
    {
        if (collision.gameObject.tag == "Player")
        {
            foreach (Collider2D mountain in mountainColliders)
            {
                // leaving restores the lower mountain barrier
                mountain.enabled = true;
            }

            foreach (Collider2D boundary in boundaryColliders)
            {
                // raised area boundaries no longer need to hold the player
                boundary.enabled = false;
            }

            collision.gameObject.GetComponent<SpriteRenderer>().sortingOrder = 5;
        }
    }
}
