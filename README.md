# Activity Daily Living (ADL) Error Detection
Program to detect error in ADL tasks.

## Requirements
Install the following python modules:
```
sudo pip install pika
sudo pip install configparser
sudo pip install typing
```

This repository has some encrypted files. You will need `git-crypt` installed and the key to decrypt the files.
```
sudo apt install git-crypt
```

#### Error Detector
Launch error detector for actual experiment
```
roslaunch adl_error_detection detect_error.launch is_test:=false
```

#### Start/End Task ROS Service Call
There are three task types: (0) Watering plants, (1) Taking medication with food, and (2) Walking dog. You can request a task to start (2) or end (3).

Example:
Request to start taking medication with food task
```
rosservice call /task_controller '{id: {stamp: now, task_number: 1}, request: {status: 2}}'
```

Request to end taking medication with food task
```
rosservice call /task_controller '{id: {stamp: now, task_number: 1}, request: {status: 3}}'
```

Writing a ROS Service client code
```python
#!/usr/bin/env python

import rospy
from ras_msgs.msg import TaskStatus, TaskId
from ras_msgs.srv import TaskController

def start_task(task_number):
    try:
        rospy.wait_for_service('task_controller')
        start = rospy.ServiceProxy('task_controller', TaskController)
        task_id = TaskId(stamp=rospy.Time.now(), task_number=task_number)
        request = TaskStatus(status=TaskStatus.START)
        response = start(task_id, request)
    except (rospy.ServiceException, rospy.ROSException), e:
        rospy.logerr("Service call failed: %s"%e)

def end_task(task_number):
    try:
        rospy.wait_for_service('task_controller')
        end = rospy.ServiceProxy('task_controller', TaskController)
        task_id = TaskId(stamp=rospy.Time.now(), task_number=task_number)
        request = TaskStatus(status=TaskStatus.END)
        response = end(task_id, request)
    except (rospy.ServiceException, rospy.ROSException), e:
        rospy.logerr("Service call failed: %s"%e)
```

#### View logs sent to CASAS
Run this launch file to view the logs sent to CASAS.
```
roslaunch adl_error_detection casas_log_observer.launch
```

#### View Transformed Robot's SLAM Location into Kyoto map
Run this node to view the transformed robot location plot
```
rosrun adl_error_detection view_robot_in_map.py
```

---

## Offline Testing of Error Detection Module
This allow us to use previously collected participant data and simulate the experiment through the experiment's CASAS logged data.

#### Error Detector
Launch error detector for testing
```
roslaunch adl_error_detection detect_error.launch is_test:=true test_error:=true use_location:=true
```

#### Publishing Log to CASAS Testbed Server
Run the node below that would wait for rosservice call where you can specify the task number and dummy data file to load. This data will be read and published to CASAS. Once a service call is sent, it will also sent a rosservice call to `task_controller` to start error detection. Arugment `1.0` is the speed of the simulation where current setup runs in real-time simulation. Lower the number to speed up simulation but BEWARE that you can clogged up the server if it's too fast.
```
rosrun adl_error_detection test_error_detector.py 1.0
```

#### Define Task and Participant Log File
Run rosservice call to specify task number and file. All participant's log file requires a full path and its file name.
```
rosservice call /test_task_controller '{request: {status: 2}, file: <full_path_to_file>}'
```

The participant's log file should already include the ROS logs that define that start and end of the experiment. They should look like the lines below. Such lines in the log is how the simulator knows when to start and end the error detection module. It also defines what task is being completed.
```
2018-06-18 16:35:27.738515	ROS_Task	{'action': 'BEGIN', 'task': 'Walk_Dog'}
...
2018-06-18 16:37:26.865256	ROS_Task	{'action': 'END', 'task': 'Walk_Dog'}
```
