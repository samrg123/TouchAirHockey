using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class scoreManager : MonoBehaviour
{
    // Start is called before the first frame update

    public int scoreOne = 0;
    public int scoreTwo = 0;
    public GameObject puckPrefab;
    GameObject puck;

    public TMP_Text textMesh;
    private string prevText = "";

    void Start()
    {
        puck = GameObject.Instantiate(puckPrefab);
        SetScoreDisplay();
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    public void SetScoreDisplay()
    {
        textMesh.text = scoreTwo + " : " + scoreOne;
    }

    public void ResetGame()
    {
        scoreOne = 0;
        scoreTwo = 0;
        ResetPuck();
        SetScoreDisplay();
    }

    public void ResetPuck()
    {
        Destroy(puck);
        puck = GameObject.Instantiate(puckPrefab);
    }

    public void TogglePause()
    {
        Rigidbody r = puck.GetComponentInChildren<Rigidbody>();
        r.isKinematic = !r.isKinematic;
        if (r.isKinematic)
        {
            prevText = textMesh.text;
            textMesh.text = "Paused";
        }
        else
        {
            textMesh.text = prevText;
        }
        
    }

    public void Score(int type)
    {
        if (type == 1)
        {
            scoreOne++;
            
        }
        else if (type == 2)
        {
            scoreTwo++;
        }
        SetScoreDisplay();
        ResetPuck();
    }
}
