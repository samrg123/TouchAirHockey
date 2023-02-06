using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;

public class interactionManager : MonoBehaviour
{

    public string inputDir = "";

    public GameObject controller_prefab;
    public GameObject controller2_prefab;

    GameObject controllerOne;
    List<GameObject> controllerOneWall;
    GameObject controllerTwo;
    List<GameObject> controllerTwoWall;

    Vector3 OneTarget;
    Vector3 TwoTarget;

    public List<Vector3> testOnePos = new List<Vector3>();
    public List<Vector3> testTwoPos = new List<Vector3>();

    private float speed = 100f;

    private float originY = 5f;
    private float lengthMulti = 73f;
    private float widthMulti = 36f;

    private float prevTime = 0f;
    private float timeOffset = 0.05f;

    public scoreManager score;
    
    // Start is called before the first frame update
    void Start()
    {
        controllerOne = GameObject.Instantiate(controller_prefab, gameObject.transform);
        controllerOne.SetActive(false);
        controllerOne.GetComponent<sliderCheck>().score_manger = score;
        controllerTwo = GameObject.Instantiate(controller2_prefab, gameObject.transform);
        controllerTwo.SetActive(false);
        controllerTwo.GetComponent<sliderCheck>().score_manger = score;
        controllerOneWall = new List<GameObject>();
        controllerTwoWall = new List<GameObject>();

    }

    // Update is called once per frame
    void Update()
    {
        if (Time.time > prevTime + timeOffset)
        {
            readInput(inputDir);
            prevTime = Time.time;
        }
        //parseInput(testOnePos, testTwoPos);

        if (controllerOne.activeSelf)
        {
            //Debug.Log(OneTarget);
            controllerOne.transform.position = Vector3.MoveTowards(controllerOne.transform.position, OneTarget, speed * Time.deltaTime);
        }
        if (controllerTwo.activeSelf)
        {
            controllerTwo.transform.position = Vector3.MoveTowards(controllerTwo.transform.position, TwoTarget, speed * Time.deltaTime);
        }
    }

    void distroyWall(int type)
    {
        if (type == 1)
        {
            foreach (GameObject obj in controllerOneWall)
            {
                Destroy(obj);
            }
            controllerOneWall.Clear();
        }
        else
        {
            foreach (GameObject obj in controllerTwoWall)
            {
                Destroy(obj);
            }
            controllerTwoWall.Clear();
        }
        
    }

    Vector3 SetYOffset(Vector3 pos)
    {
        return new Vector3(pos[0], originY, pos[2]);
    }

    void parseInput (List<Vector3> onePos, List<Vector3> twoPos)
    {
        if (onePos.Count >= 5 && twoPos.Count >= 5)
        {
            score.ResetGame();
            controllerOne.SetActive(false);
            distroyWall(1);
            controllerTwo.SetActive(false);
            distroyWall(2);
        }
        if (onePos.Count == 1)
        {
            if (onePos.Count != controllerOneWall.Count)
            {
                distroyWall(1);
            }
            if (!controllerOne.activeSelf)
            {
                controllerOne.transform.position = SetYOffset(onePos[0]);
                controllerOne.SetActive(true);
            }
            OneTarget = SetYOffset(onePos[0]);
        }
        else if (onePos.Count > 1)
        {
            if (controllerOne.activeSelf)
            {
                controllerOne.SetActive(false);
            }
            if (onePos.Count != controllerOneWall.Count)
            {
                distroyWall(1);
                foreach (Vector3 obj_pos in onePos)
                {
                    controllerOneWall.Add(GameObject.Instantiate(controller_prefab, SetYOffset(obj_pos), new Quaternion(0, 0, 0, 0)));
                }
            }
        }
        else
        {
            controllerOne.SetActive(false);
            distroyWall(1);
        }
        if (twoPos.Count == 1)
        {
            if (twoPos.Count != controllerTwoWall.Count)
            {
                distroyWall(2);
            }
            if (!controllerTwo.activeSelf)
            {
                controllerTwo.transform.position = SetYOffset(twoPos[0]);
                controllerTwo.SetActive(true);
            }
            TwoTarget = SetYOffset(twoPos[0]);
        }
        else if (twoPos.Count > 1)
        {
            if (controllerTwo.activeSelf)
            {
                controllerTwo.SetActive(false);
            }
            if (twoPos.Count != controllerTwoWall.Count)
            {
                distroyWall(2);
                foreach (Vector3 obj_pos in twoPos)
                {
                    controllerTwoWall.Add(GameObject.Instantiate(controller2_prefab, SetYOffset(obj_pos), new Quaternion(0, 0, 0, 0)));
                }
            }
        }
        else
        {
            controllerTwo.SetActive(false);
            distroyWall(2);
        }
    }


    void readInput(string dir)
    {
        List<Vector3> onePos = new List<Vector3>();
        List<Vector3> twoPos = new List<Vector3>();

        /*
         * put file read and parse function here
         * 
         */

        StreamReader reader = new StreamReader(this.inputDir);

        List<string> lines = new List<string>();
        while(!reader.EndOfStream)
        {
            string line = reader.ReadLine();
            //Debug.Log(line);
            lines.Add(line);
            
        }
        reader.Close();
        foreach (string line in lines) {
            string[] parsedLine = line.Split(char.Parse(" "));
            float x = float.Parse(parsedLine[3]);
            x = lengthMulti * x;
            float z = float.Parse(parsedLine[5]);
            z = widthMulti * z;
            if (x < 0)
            {
                onePos.Add(new Vector3(x, originY, z));
            }
            else
            {
                twoPos.Add(new Vector3(x, originY, z));
            }
        }

        parseInput(onePos, twoPos);
        
    }
}
