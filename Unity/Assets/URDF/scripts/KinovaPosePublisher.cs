using System;
using Oculus.Interaction.Input;
using RosMessageTypes.BuiltinInterfaces;
using RosMessageTypes.Geometry;
using RosMessageTypes.Std;
using TMPro;
using Unity.Robotics.ROSTCPConnector;
using Unity.Robotics.ROSTCPConnector.ROSGeometry;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Publica en /controller (geometry_msgs/PoseStamped) la posición de la mano
/// derecha relativa a la base del robot, una vez por cada pinch. El botón
/// asociado (OnButtonClick) envía la pose fija "Home" (0.5, 0.5, 0.5).
/// Sustituye a KinovaPublisher.cs (ROS#) con ROS-TCP-Connector.
/// </summary>
[RequireComponent(typeof(Button))]
public class KinovaPosePublisher : MonoBehaviour
{
    public string topicName = "/controller";
    public TextMeshProUGUI poseText;
    public GameObject RobotBaseTransform;
    public string FrameId = "base_link";
    public Hand RHand;
    public Transform RightHand;

    private ROSConnection ros;
    private bool hasPublishedDuringPinch = false;

    private void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.RegisterPublisher<PoseStampedMsg>(topicName);
    }

    private void FixedUpdate()
    {
        if (IsRightPinching())
        {
            if (!hasPublishedDuringPinch)
            {
                UpdateMessage();
                hasPublishedDuringPinch = true;
            }
        }
        else
        {
            hasPublishedDuringPinch = false;
        }
    }

    public void OnButtonClick()
    {
        Publish(new PointMsg(0.5, 0.5, 0.5));
        if (poseText != null)
        {
            poseText.text = "Home";
        }
    }

    private void UpdateMessage()
    {
        if (RobotBaseTransform == null)
        {
            Debug.LogError("RobotBaseTransform not asigned");
            return;
        }

        Vector3 localPosition = RobotBaseTransform.transform.InverseTransformPoint(RightHand.position);
        PointMsg position = localPosition.To<FLU>();
        Publish(position);

        if (poseText != null)
        {
            poseText.text = $"Posición relativa enviada:\n" +
                            $"({position.x:F2}, {position.y:F2}, {position.z:F2})";
        }
    }

    private void Publish(PointMsg position)
    {
        var msg = new PoseStampedMsg
        {
            header = new HeaderMsg { frame_id = FrameId, stamp = Now() },
            pose = new PoseMsg(position, new QuaternionMsg(0, 0, 0, 1)),
        };
        ros.Publish(topicName, msg);
    }

    /// <summary>Hora UTC actual como builtin_interfaces/Time (sec es int en ROS2, uint en ROS1).</summary>
    private static TimeMsg Now()
    {
        long ticks = DateTime.UtcNow.Ticks - DateTime.UnixEpoch.Ticks;
        uint nanosec = (uint)(ticks % TimeSpan.TicksPerSecond * 100);
#if ROS2
        return new TimeMsg((int)(ticks / TimeSpan.TicksPerSecond), nanosec);
#else
        return new TimeMsg((uint)(ticks / TimeSpan.TicksPerSecond), nanosec);
#endif
    }

    private bool IsRightPinching()
    {
        return RHand != null && RHand.GetIndexFingerIsPinching();
    }
}
