#!/usr/bin/env python

import rospy
from visualization_msgs.msg import Marker
import re
import tf2_ros
import geometry_msgs.msg
"""
user:~$ rosmsg show visualization_msgs/Marker
uint8 ARROW=0
uint8 CUBE=1
uint8 SPHERE=2
uint8 CYLINDER=3
uint8 LINE_STRIP=4
uint8 LINE_LIST=5
uint8 CUBE_LIST=6
uint8 SPHERE_LIST=7
uint8 POINTS=8
uint8 TEXT_VIEW_FACING=9
uint8 MESH_RESOURCE=10
uint8 TRIANGLE_LIST=11
uint8 ADD=0
uint8 MODIFY=0
uint8 DELETE=2
uint8 DELETEALL=3
std_msgs/Header header
  uint32 seq
  time stamp
  string frame_id
string ns
int32 id
int32 type
int32 action
geometry_msgs/Pose pose
  geometry_msgs/Point position
    float64 x
    float64 y
    float64 z
  geometry_msgs/Quaternion orientation
    float64 x
    float64 y
    float64 z
    float64 w
geometry_msgs/Vector3 scale
  float64 x
  float64 y
  float64 z
std_msgs/ColorRGBA color
  float32 r
  float32 g
  float32 b
  float32 a
duration lifetime
bool frame_locked
geometry_msgs/Point[] points
  float64 x
  float64 y
  float64 z
std_msgs/ColorRGBA[] colors
  float32 r
  float32 g
  float32 b
  float32 a
string text
string mesh_resource
bool mesh_use_embedded_materials
"""

class GetObjectsPosition():

    SURFACE_OBJECTS_TOPIC_NAME = "surface_objects"
    EXPECTED_TABLE_HEIGHT = 0.91
    HEIGHT_FUZZ = 0.06
    Y_MAX = 0.1

    GRASPABLE_OBJECT_NAME = "graspable_object"
    GRASPABLE_OBJECT_PARENT_FRAME = "pc_cam_base_link"
    
    def __init__(self):
        self._surface_objects_sub = rospy.Subscriber(
                GetObjectsPosition.SURFACE_OBJECTS_TOPIC_NAME,
                Marker,
                self.__surface_objects_callback)
        self._ctrl_c = False
        rospy.on_shutdown(self.__shutdownhook)
        self._br = tf2_ros.TransformBroadcaster()
    
    def __surface_objects_callback(self, marker: Marker):
        p = re.compile(r"surface_\d*_object_\d*_axes")
        y = marker.pose.position.y
        height = marker.pose.position.z
        status = None
        if p.fullmatch(marker.ns) and \
            (abs(height - GetObjectsPosition.EXPECTED_TABLE_HEIGHT) < \
                GetObjectsPosition.HEIGHT_FUZZ) and \
            marker.type == 3:
            status = "Accepted"
            self.__publish_graspable_object(marker)
        else:
            status = "Rejected"
        rospy.logdebug(f"{status}: {marker.ns=} {height=} {marker.type=} {y=}")
    
    def __publish_graspable_object(self, marker: Marker):
        t = geometry_msgs.msg.TransformStamped()
        t.header.stamp = rospy.Time.now()
        t.header.frame_id = GetObjectsPosition.GRASPABLE_OBJECT_PARENT_FRAME
        t.child_frame_id = GetObjectsPosition.GRASPABLE_OBJECT_NAME
        
        t.transform.translation = marker.pose.position
        t.transform.rotation = marker.pose.orientation

        rospy.loginfo(f"Publish transform: {t}")
        
        self._br.sendTransform(t)

    def __shutdownhook(self):
        self.ctrl_c = True
            
if __name__ == '__main__':
    rospy.init_node("get_objects_position", anonymous=True)
    GetObjectsPosition()
    rospy.spin()