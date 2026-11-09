using System.Collections.Generic;
using RosMessageTypes.Sensor;
using Unity.Robotics.ROSTCPConnector;
using Unity.Robotics.UrdfImporter;
using UnityEngine;

/// <summary>
/// Suscribe /joint_states (sensor_msgs/JointState, rad) y pone el xDrive.target
/// (grados) del ArticulationBody de cada UrdfJoint del robot importado con el
/// mismo jointName. Los nombres que no existen en el robot se ignoran.
/// </summary>
public class KinovaJointStateSubscriber : MonoBehaviour
{
    public string topicName = "/joint_states";
    public GameObject robotRoot;

    private readonly Dictionary<string, ArticulationBody> joints = new Dictionary<string, ArticulationBody>();

    private void Start()
    {
        if (robotRoot == null)
        {
            Debug.LogError("KinovaJointStateSubscriber: robotRoot no asignado");
            return;
        }

        foreach (var joint in robotRoot.GetComponentsInChildren<UrdfJoint>())
        {
            var body = joint.GetComponent<ArticulationBody>();
            if (body != null && !string.IsNullOrEmpty(joint.jointName))
            {
                joints[joint.jointName] = body;
            }
        }

        ROSConnection.GetOrCreateInstance().Subscribe<JointStateMsg>(topicName, OnJointState);
    }

    private void OnJointState(JointStateMsg msg)
    {
        int n = Mathf.Min(msg.name.Length, msg.position.Length);
        for (int i = 0; i < n; i++)
        {
            if (joints.TryGetValue(msg.name[i], out var body))
            {
                var drive = body.xDrive;
                drive.target = (float)(msg.position[i] * Mathf.Rad2Deg);
                body.xDrive = drive;
            }
        }
    }
}
