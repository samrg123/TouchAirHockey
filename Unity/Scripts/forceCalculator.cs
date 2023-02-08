using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class forceCalculator : MonoBehaviour
{

    float force = 0f;
    List<float> speedArray = new List<float>();
    private int recordSizeThresh = 5;
    Rigidbody rig;
    public float mess = 5f;
    private Vector3 prevLocation;
    private float prevTime;
    private float timeOffset = 0.05f;

    // Start is called before the first frame update
    void Start()
    {
        rig = gameObject.GetComponent<Rigidbody>();
        prevLocation = transform.position;
    }

    // Update is called once per frame
    void Update()
    {
        if (Time.time > prevTime + timeOffset)
        {
            if (speedArray.Count > recordSizeThresh)
            {
                speedArray.RemoveAt(0);
            }
            Vector3 velocity = (transform.position - prevLocation) / Time.deltaTime;
            speedArray.Add(velocity.magnitude);
            prevLocation = transform.position;
            prevTime = Time.time;
        }
        
        //GetAcceleration();
    }

    public float GetAcceleration()
    {
        float acce_sum = 0;
        for (int i = 0; i < speedArray.Count - 1; i++)
        {
            acce_sum += (speedArray[i + 1] - speedArray[i]);
        }
        return acce_sum / (speedArray.Count - 1);
    }

    public Vector3 GetForce(Vector3 direction)
    {
        Debug.Log(direction);
        Debug.Log(this.GetAcceleration());
        Debug.Log(Vector3.Normalize(transform.position - prevLocation) * mess * this.GetAcceleration());
        return Vector3.Dot(Vector3.Normalize(transform.position - prevLocation) * mess * this.GetAcceleration(), Vector3.Normalize(direction)) * Vector3.Normalize(direction);
    }
}
