#!/usr/bin/env python

import rospy
import rospkg
import datetime
import logging
import configparser
import yaml
import math
import sys

from collections import deque
from actionlib import SimpleActionClient
from actionlib_msgs.msg import GoalStatus
from adl import check_sequence_gen, check_sequence_wloc_gen
from adl.util import Items, TaskToDag, Locations
from adl.util import WaterPlantsDag, WalkDogDag, TakeMedicationDag
from adl.util import ConnectPythonLoggingToRos
from adl.util import Task, Goal, Status
from adl.util import get_mac, bcolors
from adl.robot_sensor_translation import convert_point, RobotXYViz
from casas import objects, rabbitmq
from casas.publish import PublishToCasas

from ras_msgs.msg import DoErrorAction, DoErrorGoal
from ras_msgs.msg import TaskStatus
from ras_msgs.msg import RobotToMapTransformState
from ras_msgs.srv import TaskController, TaskControllerResponse
from ras_msgs.srv import Pause


class ErrorDetector:

    def __init__(self):
        rospy.loginfo("error_detector: Initializing error detector")

        rospack = rospkg.RosPack()
        self.pkg_path = rospack.get_path('adl_error_detection')

        self.mac_address = get_mac()
        self.print_casas_log = True
        self.all_sensors = deque()
        self.sensors = deque()

        self.test = True
        self.test_error = False
        self.use_location = True
        self.plot_robot_location = False
        if rospy.has_param("adl"):
            adl = rospy.get_param("adl")
            self.test = adl['is_test']
            self.test_error = adl['test_error']
            self.use_location = adl['use_location']
            self.plot_robot_location = adl['plot_robotxy']
        self.task_status = TaskStatus()

        self.task_setup()
        self.ros_setup()

        if self.plot_robot_location:
            self.rviz = RobotXYViz(name='kyoto-error_detector', visible=False)

        # CASAS Sensors
        config = configparser.ConfigParser()
        config.read(self.pkg_path + "/scripts/casas.cfg")
        default = config['DEFAULT']

        self.translate = dict()
        self.rcon = rabbitmq.Connection(
            agent_name=rospy.get_name(),
            amqp_user=default['AmqpUser'],
            amqp_pass=default['AmqpPass'],
            amqp_host=default['AmqpHostDev'] if self.test_error or self.test else default['AmqpHost'],
            amqp_port=default['AmqpPort'],
            amqp_vhost=default['AmqpVHost'],
            amqp_ssl=default.getboolean('AmqpSSL'),
            translations=self.translate)
        self.rcon.l.addHandler(ConnectPythonLoggingToRos())
        self.casas_setup_exchange()

        rospy.Timer(rospy.Duration(.01), self.casas_logging, oneshot=True)

    def casas_logging(self, event):
        # CASAS Logging
        self.casas = PublishToCasas(
            agent_num='1', node='ROS_Node_'+rospy.get_name()[1:],
            test=self.test or self.test_error) # use the test agent instead of kyoto if true
        try:
            self.casas.connect()
        finally:
            rospy.signal_shutdown("Cannot connect to CASAS! Need to restart.")
            self.casas.finish()

    def task_setup(self, task_num=-1, status=TaskStatus.PENDING, text="PENDING"):
        self.task_number = task_num
        self.task_status.status = status
        self.task_status.text = text
        self.task_sequence = []
        self.task_locations = []
        self.task_pause = False
        self.task_dag = None
        self.error_key = None
        self.last_key = None
        self.sensors.clear()
        if self.task_number >= 0:
            self.task_dag = TaskToDag.mapping[self.task_number][1 if self.use_location else 0].task_start
        self.check_sequence = check_sequence_wloc_gen if self.use_location else check_sequence_gen
        self.is_detect_error_gen_created = False

    def ros_setup(self):
        rospy.Timer(rospy.Duration(0.1), self.__error_detection_cb, oneshot=True)

        # Publish topic robot (x,y) to map (x,y) point
        self.robot_to_map_pub = rospy.Publisher('/robot_to_map_xy', RobotToMapTransformState, queue_size=5)

        # start task rosservice server
        self.task_service = rospy.Service(
            'task_controller', TaskController,
            self.task_controller)
        rospy.loginfo("error_detector: task_controller service running")

        self.do_error = SimpleActionClient('do_error', DoErrorAction)
        self.do_error_connected = True
        if not self.do_error.wait_for_server(rospy.Duration(3)):
            self.do_error_connected = False
            rospy.logerr("error_detector: do_error client failed to connect")
            return

    def pause_dummy_data(self, request):
        rospy.wait_for_service('pause')
        try:
            pause = rospy.ServiceProxy('pause', Pause)
            response = pause(request)
            return response.success
        except rospy.ServiceException, e:
            rospy.logerr("Service call failed: {}".format(e))

    def start_error_correction(self, error_status):
        self.is_detect_error_gen_created = False
        self.detect_error_gen.close()
        self.error_key = error_status[4]
        self.error_step = TaskToDag.mapping[self.task_number][1 if self.use_location else 0].subtask[self.error_key]
        self.last_key = self.error_key
        rospy.logwarn("error_detector: Initiating error correction for {} at step {}".format(
            self.error_key, self.error_step))

        if self.do_error_connected:
            goal = DoErrorGoal()
            goal.task_number = self.task_number
            goal.error_step = self.error_step
            self.do_error.send_goal(
                goal,
                done_cb=self.__error_correction_done_cb,
                active_cb=self.__error_correction_active_cb,
                feedback_cb=self.__error_correction_feedback_cb)

    def __error_correction_feedback_cb(self, feedback):
        rospy.loginfo("error_detector: do_error correction={}".format(feedback.text))

    def __error_correction_active_cb(self):
        self.task_pause = True
        self.task_status.text = "ERROR CORRECTION STARTED"
        self.casas.publish(
            package_type='ROS',
            sensor_type='ROS_Task_Step_Error',
            serial=self.mac_address,
            target='ROS_Task_Step_Fix_Error',
            message={
                'action':'START',
                'task':Task.types[self.task_number],
                'error_step':str(self.error_step),
                'error_id':self.error_key},
            category='state'
        )

    def __error_correction_done_cb(self, terminal_state, result):
        result_bool = (result.status == Status.COMPLETED)
        if terminal_state == GoalStatus.SUCCEEDED and result_bool:
            self.task_status.text = "ERROR CORRECTION SUCCEEDED"
            rospy.loginfo("error_detector: do_error correction succeeded")
            self.__correct_sequence()
            self.casas.publish(
                package_type='ROS',
                sensor_type='ROS_Task_Step_Error',
                serial=self.mac_address,
                target='ROS_Task_Step_Fix_Error',
                message={
                    'action':'SUCCEEDED',
                    'task':Task.types[self.task_number],
                    'error_step':str(self.error_step),
                    'error_id':self.error_key},
                category='state'
            )
            if self.test_error:
                self.pause_dummy_data(False)
        elif terminal_state == GoalStatus.SUCCEEDED and result.status == Status.FAILED:
            self.task_status.text = "ERROR CORRECTION FAILED"
            rospy.logerr("error_detector: do_error correction failed")
            self.casas.publish(
                package_type='ROS',
                sensor_type='ROS_Task_Step_Error',
                serial=self.mac_address,
                target='ROS_Task_Step_Fix_Error',
                message={
                    'action':'FAILED',
                    'error_step':str(self.error_step),
                    'task':Task.types[self.task_number]},
                category='state'
            )
        else:
            rospy.logwarn("error_detector: do_error preempted or cancelled")

        self.task_pause = False

    def __correct_sequence(self):
        self.task_dag = TaskToDag.mapping[self.task_number][1 if self.use_location else 0].subtask_info[self.error_step][4]
        self.task_sequence = []
        self.task_locations = []

    def stop_error_correction(self):
        if self.do_error_connected:
            if self.task_pause and self.do_error.get_state() == GoalStatus.ACTIVE:
                self.do_error.cancel_goal()
                rospy.logwarn("error_detector: do_error correction cancelled")
                self.casas.publish(
                    package_type='ROS',
                    sensor_type='ROS_Task_Step_Error',
                    serial=self.mac_address,
                    target='ROS_Task_Step_Fix_Error',
                    message={
                        'action':'CANCELLED',
                        'error_step':str(self.error_step),
                        'task':Task.types[self.task_number]},
                    category='state'
                )

    def task_controller(self, request):
        response = TaskStatus(
            status=TaskStatus.SUCCESS,
            text='SUCCESS')

        if request.id.task_number < Task.size:
            if self.task_number < 0 \
               and request.request.status == TaskStatus.START \
               and self.task_status.status == TaskStatus.PENDING:
                self.task_setup(
                    task_num=request.id.task_number,
                    status=TaskStatus.ACTIVE,
                    text="ACTIVE")
                self.last_task_number = request.id.task_number
                self.current_location = 'L'
                rospy.loginfo("error_detector: {}=START".format(Task.types[self.task_number]))
                self.casas.publish(
                    package_type='ROS',
                    sensor_type='ROS_Task',
                    serial=self.mac_address,
                    target='ROS_Task',
                    message={'action':'BEGIN', 'task':Task.types[self.task_number]},
                    category='state'
                )
                return TaskControllerResponse(response)

            elif self.task_number == request.id.task_number \
                    and request.request.status == TaskStatus.END \
                    and self.task_status.status == TaskStatus.ACTIVE:
                self.stop_error_correction()
                self.task_setup()
                rospy.loginfo("error_detector: {}=END".format(Task.types[request.id.task_number]))
                self.casas.publish(
                    package_type='ROS',
                    sensor_type='ROS_Task',
                    serial=self.mac_address,
                    target='ROS_Task',
                    message={'action':'END', 'task':Task.types[request.id.task_number]},
                    category='state'
                )
                return TaskControllerResponse(response)

        rospy.logwarn("task request invalid")
        response.status = TaskStatus.FAILED
        response.text = "FAILED"
        return TaskControllerResponse(response)

    def casas_setup_exchange(self):
        if self.test_error:
            self.rcon.setup_subscribe_to_exchange(
                exchange_name='test.events.testbed.casas',
                exchange_type='topic',
                routing_key='#',
                exchange_durable=True,
                casas_events=True,
                callback_function=self.__casas_cb)
        else:
            self.rcon.setup_subscribe_to_exchange(
                exchange_name='all.events.testbed.casas',
                exchange_type='topic',
                routing_key='#',
                exchange_durable=True,
                casas_events=True,
                callback_function=self.__casas_cb)

    def __is_exclude(self, task_number, sensor):
        if (task_number in [Task.WATER_PLANTS, Task.TAKE_MEDS]) and (sensor in ['M056', 'M057']):
            # In TAKE_MEDS | WATER_PLANTS task,
            # when participant is at M018, it also triggers
            # hallway sensors M056 and M057 due to cateye sensors
            return True
        elif (task_number in [Task.WATER_PLANTS, Task.TAKE_MEDS]) and (sensor == 'M023'):
            # Can sometimes get triggered when participant walks by
            return True
        elif sensor == 'M060':
            # Starting 7/19/2018, all experiments shows that M060 is getting
            # triggered by participant while at M007 and M008.
            return True
        elif sensor in ['M004', 'M005', 'M012', 'M011']:
            # When teleop was used in early participants, navigator
            # stayed below these sensors
            return True
        # Other excluded sensors (excluded in items.py)
        # M004, M005, M012, M011 - navigator position
        # M001 - too close to M023 (hallway)
        # M015 - too close to M016 (kitchen)
        # MA### - area sensors are too general and are triggerd by navigator
        return False

    def __add_sensor_to_sequence(self, sensor, loc):
        is_estimote = sensor.target[:3] == 'EST' \
            and sensor.message == 'MOVED'
        is_door_closed = sensor.target in ['D001', 'D011'] \
            and sensor.message == 'CLOSE'
        is_ambient_sensor = sensor.target[0] == 'M' and sensor.message == 'ON'
        new_loc = None
        is_added = False

        #Ambient sensors
        if is_ambient_sensor and sensor.target in Locations.decode.keys():
            if self.__is_exclude(self.task_number, sensor.target):
                return False

            new_loc = Locations.decode[sensor.target]
            if self.current_location != new_loc:
                if self.use_location:
                    self.sensors.append(('{}>{}'.format(self.current_location, new_loc), ''))
                    is_added = True
                self.current_location = new_loc
                rospy.loginfo("{}current location: {}{}".format(bcolors.WARNING, Locations.encode[self.current_location][1], bcolors.ENDC))
        #Estimotes + Door sensors
        elif is_estimote or is_door_closed:
            code = Items.decode[sensor.target]
            # Only include item used in the task
            if self.task_number in Items.encode[code][2]:
                self.sensors.append((code, loc))
                is_added = True
        return is_added

    def __check_error(self, new_sequence, new_location):
        if self.task_dag is None: # Task Completed
            task_end = TaskToDag.mapping[self.task_number][1 if self.use_location else 0].task_end
            task_key = task_end['current']
            task_step = TaskToDag.mapping[self.task_number][1 if self.use_location else 0].subtask[task_key]
            result = (task_step, True, task_end['current'], True, 'Done')
        else:
            if not self.is_detect_error_gen_created:
                task_key = self.task_dag['current']
                task_step = TaskToDag.mapping[self.task_number][1 if self.use_location else 0].subtask[task_key]
                self.detect_error_gen = self.check_sequence(
                    self.task_dag,
                    task_step_num=task_step,
                    num_tasks=TaskToDag.mapping[self.task_number][1 if self.use_location else 0].num_tasks,
                    current=self.task_dag['current'])
                self.is_detect_error_gen_created = True

            next(self.detect_error_gen)
            if self.use_location:
                result = self.detect_error_gen.send((new_sequence, new_location))
            else:
                result = self.detect_error_gen.send(new_sequence)

        rospy.logdebug("error_detector: {}".format(result))
        return result

    def __error_detection(self):
        if len(self.sensors) > 0:
            new_seq, new_loc = self.sensors.popleft()
            check_result = self.__check_error(new_seq, new_loc)
            is_error_detected = not check_result[1] and not check_result[3]

            # Concatenate new sensor readings into task sequence
            self.task_sequence.append((new_seq, new_loc))
            if self.test:
                rospy.logdebug("seq :{}".format("-".join(map(str, self.task_sequence))))

            # Error Detected
            if is_error_detected:
                self.task_pause = True
                # if self.test_error:
                #     self.pause_dummy_data(True)

                if self.plot_robot_location:
                    self.rviz.save_image("/home/brownyoda/Projects/RAS/{}.png".format(check_result[4]))

                # Empty out sensors queue
                self.sensors.clear()
                # Start error correction
                self.start_error_correction(check_result)
                # if self.test_error:
                #     self.stop_error_correction()
                #     self.__correct_sequence()
                #     self.pause_dummy_data(False)
                #     self.task_pause = False

            # No Error Detected
            else:
                # Check if a new step is completed in the sequence
                if check_result[2] != check_result[4] and self.last_key != check_result[2] and check_result[1]:
                    self.current_step = TaskToDag.mapping[self.task_number][1 if self.use_location else 0].subtask[check_result[2]]
                    self.casas.publish(
                        package_type='ROS',
                        sensor_type='ROS_Task_Step',
                        serial=self.mac_address,
                        target='ROS_Task_Step',
                        message={
                            'task':Task.types[self.task_number],
                            'step':str(self.current_step),
                            'id':check_result[2]},
                        category='state'
                    )
                    rospy.loginfo('{}{} Task --- step {}: {} completed{}'.format(bcolors.OKGREEN, Task.types[self.task_number], self.current_step, check_result[2], bcolors.ENDC))
                    rospy.loginfo("{}next step: {}{}".format(bcolors.OKBLUE, check_result[4], bcolors.ENDC))
                    # NEW: exclude completed sequence
                    self.task_dag = TaskToDag.mapping[self.last_task_number if self.task_number < 0 else self.task_number][1 if self.use_location else 0].subtask_info[self.current_step+1][3]
                    self.task_sequence = []
                    self.task_locations = []
                    self.last_key = check_result[2]

    def __error_detection_cb(self, event):
        while not rospy.is_shutdown():
            try:
                if len(self.all_sensors) > 0:
                    sensor, pause = self.all_sensors.popleft()
                    #if self.task_pause:
                    if pause:
                        # While pause, still update location
                        is_ambient_sensor = sensor.target[0] == 'M' and sensor.message == 'ON'
                        if is_ambient_sensor and sensor.target in Locations.decode.keys():
                            if not self.__is_exclude(self.task_number, sensor.target):
                                self.current_location = Locations.decode[sensor.target]
                                rospy.loginfo("{}current location: {}{}".format(bcolors.WARNING, Locations.encode[self.current_location][1], bcolors.ENDC))

                    elif self.task_status.status == TaskStatus.ACTIVE and not pause: #not self.task_pause:
                        if self.__add_sensor_to_sequence(sensor, self.current_location):
                            # Only check for error if sensor was added to the sequence
                            self.__error_detection()

                    if sensor.target == 'ROS_XYR':
                        xyr = yaml.load(sensor.message)
                        x = float(xyr['x'])
                        y = float(xyr['y'])
                        x, y = convert_point((x, y))
                        state = RobotToMapTransformState()
                        state.pose.x = x
                        state.pose.y = y
                        state.pose.theta = -1 # TODO: requires transformation
                        state.reset = False
                        self.robot_to_map_pub.publish(state)
                        if self.plot_robot_location:
                            self.rviz.add_point(x, y)

                    elif sensor.target == 'ROS_Task':
                        msg = yaml.load(sensor.message)
                        if msg['action'] == 'END':
                            state = RobotToMapTransformState()
                            state.pose.x = -1
                            state.pose.y = -1
                            state.pose.theta = -1 # TODO: requires transformation
                            state.reset = True
                            self.robot_to_map_pub.publish(state)
                            if self.plot_robot_location:
                                self.rviz.save_image("/home/brownyoda/Projects/RAS/{}.png".format(msg['task']))
                                self.rviz.reset()

                    if self.test_error:
                        if sensor.target == 'ROS_Task_Step_Fix_Error':
                            msg = yaml.load(sensor.message)
                            if msg['action'] == 'SUCCEEDED' and self.task_pause:
                                self.stop_error_correction()
                                self.__correct_sequence()
                                # self.pause_dummy_data(False)
                                self.task_pause = False

            # except KeyError, e:
            #     rospy.logerr("KeyError possibly due to thread race - reason {}".format(e))

            except KeyboardInterrupt:
                break

    def __casas_cb(self, sensors):
        for sensor in sensors:
            self.all_sensors.append((sensor, self.task_pause))
            sensor_str = "{}\t{}\t{}".format(
                str(sensor.stamp), str(sensor.target), str(sensor.message))
            if self.test_error:
                if sensor.target == 'ROS_Task_Step':
                    sensor_str = '{}{}{}{}'.format(bcolors.BOLD,bcolors.OKGREEN, sensor_str, bcolors.ENDC)
                elif sensor.target == 'ROS_Task_Step_Fix_Error':
                    sensor_str = '{}{}{}{}'.format(bcolors.BOLD,bcolors.WARNING, sensor_str, bcolors.ENDC)
            rospy.loginfo(sensor_str)

    def casas_run(self):
        try:
            self.rcon.run()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        rospy.loginfo("error_detector: disconnecting casas connection")
        self.rcon.stop()
        self.casas.finish()


if __name__ == "__main__":
    rospy.init_node(
        "error_detector",
        disable_signals=True,
        log_level=rospy.DEBUG if sys.argv[1] == 'true' else rospy.INFO)
    ed = ErrorDetector()
    ed.casas_run()
    rospy.on_shutdown(ed.stop)
