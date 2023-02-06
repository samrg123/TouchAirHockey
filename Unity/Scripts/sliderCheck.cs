using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class sliderCheck : MonoBehaviour
{

    public int collision_cnt = 0;
    private float prev_time = 0;
    private float reset_time = 5f;
    public scoreManager score_manger;

    // Start is called before the first frame update
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        if (collision_cnt > 8)
        {
            score_manger.TogglePause();
            collision_cnt = 0;
        }
        else if (collision_cnt != 0 && Time.time > prev_time + reset_time)
        {
            collision_cnt = 0;
        }
        
    }

    private void OnTriggerEnter(Collider other)
    {
        if (other.tag == "slider")
        {
            Debug.Log(collision_cnt);
            collision_cnt++;
            prev_time = Time.time;
        }
    }
}
