using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class goalCheck : MonoBehaviour
{

    public scoreManager scoreManager;
    public int type;

    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    void OnTriggerEnter(Collider other)
    {
        if (other.tag == "Puck")
        {
            scoreManager.Score(type);
            scoreManager.ResetPuck();
        }
    }
}
