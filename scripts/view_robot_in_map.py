#!/usr/bin/env python

import rospy
import signal

from adl.robot_sensor_translation import RobotXYViz
from ras_msgs.msg import RobotToMapTransformState

class PlotRobotInMap(object):

    def __init__(self):
        self.rviz = RobotXYViz(name='kyoto-viewer', visible=True)
        rospy.Subscriber('/robot_to_map_xy', RobotToMapTransformState, self.robot_to_map_xy_cb)

    def robot_to_map_xy_cb(self, msg):
        """
        Subscriber callback to get robot to map state
        """
        if msg.reset:
            self.rviz.reset()
        else:
            self.rviz.add_point(msg.pose.x, msg.pose.y)

if __name__ == "__main__":
    rospy.init_node("view_robot_in_map", disable_signals=True, log_level=rospy.INFO)
    plot = PlotRobotInMap()
