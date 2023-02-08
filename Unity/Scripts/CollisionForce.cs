using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CollisionForce : MonoBehaviour
{

    Rigidbody rig;
    private float forceMultiplier = 50f;
    private float distThresh = 2f;

    // Start is called before the first frame update
    void Start()
    {
        rig = gameObject.GetComponent<Rigidbody>();
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    private void OnTriggerStay(Collider other)
    {
        if (other.tag == "Controller")
        {
            Vector3 direction = gameObject.transform.position - other.transform.position;
            direction.y = 0;
            Debug.Log(direction.magnitude);
            if (direction.magnitude < distThresh)
            {
                gameObject.transform.position = new Vector3(other.transform.position.x, gameObject.transform.position.y, other.transform.position.z) + Vector3.Normalize(direction) * distThresh;
                Vector3 force = direction * forceMultiplier * 10f ;
                rig.AddForce(force);
                Debug.Log("#force");
                Debug.Log(force);
            }
            else
            {
                Vector3 force = other.gameObject.GetComponent<forceCalculator>().GetForce(direction);
                Debug.Log("#natural");
                Debug.Log(force);
                rig.AddForce(force * forceMultiplier);
            }
        }
    }

    /*
    void OnTriggerEnter(Collider other)
    {
        if (other.tag == "Controller")
        {
            Vector3 direction = gameObject.transform.position - other.transform.position;
            direction.y = 0;
            Debug.Log(direction.magnitude);
            if (direction.magnitude < distThresh)
            {
                gameObject.transform.position = other.transform.position + Vector3.Normalize(direction) * distThresh;
                Vector3 force = direction * forceMultiplier;
                rig.AddForce(force);
                Debug.Log("#");
                Debug.Log(force);
            }
            else
            {
                Vector3 force = other.gameObject.GetComponent<forceCalculator>().GetForce(direction);
                Debug.Log(force);
                rig.AddForce(force * forceMultiplier);
            }
            
        }
    }
    */
}
