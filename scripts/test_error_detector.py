#!/usr/bin/env python

import rospy
import rospkg
import datetime
import logging
import configparser
import csv
import uuid
import time
import sys
import threading

from collections import defaultdict, deque
from adl.util import ConnectPythonLoggingToRos
from adl.util import Task
from adl.util import get_mac
from casas import objects, rabbitmq

from ras_msgs.msg import TaskStatus, TaskId
from ras_msgs.srv import TestTaskController, TestTaskControllerResponse
from ras_msgs.srv import TaskController, Pause, PauseResponse

class TestErrorDetector:

    def __init__(self, speed=1):
        rospy.loginfo("Initializing Test Error Detector")

        rospack = rospkg.RosPack()
        self.pkg_path = rospack.get_path('adl_error_detection')

        self.mac_address = get_mac()
        self.speed = speed
        self.pause = False
        self.task_number = None
        self.thread = None
        self.task_status = TaskStatus(
            status=TaskStatus.PENDING,
            text='PENDING')

        config = configparser.ConfigParser()
        config.read(self.pkg_path + "/scripts/casas.cfg")
        default = config['DEFAULT']

        self.translate = dict()
        self.rcon = rabbitmq.Connection(
            agent_name=rospy.get_name(),
            amqp_user=default['AmqpUser'],
            amqp_pass=default['AmqpPass'],
            amqp_host=default['AmqpHostDev'],
            amqp_port=default['AmqpPort'],
            amqp_vhost=default['AmqpVHost'],
            amqp_ssl=default.getboolean('AmqpSSL'),
            translations=self.translate)
        self.rcon.l.addHandler(ConnectPythonLoggingToRos())
        self.rcon.set_on_connect_callback(self.casas_on_connect)
        self.rcon.set_on_disconnect_callback(self.casas_on_disconnect)

        self.ros_setup()

    def casas_on_connect(self):
        self.pause = False
        if self.thread is None or not self.thread.isAlive():
            self.thread = threading.Thread(target=self.casas_publish_event)
            self.thread.daemon = True
            self.thread.start()
        rospy.loginfo("Connected to CASAS")

    def casas_on_disconnect(self):
        self.pause = True
        rospy.logerr("Disconnected from CASAS")

    def ros_setup(self):
        # start task rosservice server
        self.task_service = rospy.Service(
            'test_task_controller', TestTaskController,
            self.test_task_controller)
        rospy.loginfo("test_task_controller service running")
        self.pause_service = rospy.Service(
            'pause', Pause,
            self.pause_dummy_publish)

    def start_task(self, task_number=None):
        try:
            rospy.wait_for_service('task_controller', timeout=2.0)
            start = rospy.ServiceProxy('task_controller', TaskController)
            task_id = TaskId(stamp=rospy.Time.now(), task_number=task_number)
            request = TaskStatus(status=TaskStatus.START)
            response = start(task_id, request)
        except (rospy.ServiceException, rospy.ROSException), e:
            rospy.logerr("Service call failed: {}".format(e))

    def end_task(self, task_number=None):
        try:
            rospy.wait_for_service('task_controller', timeout=2.0)
            end = rospy.ServiceProxy('task_controller', TaskController)
            task_id = TaskId(stamp=rospy.Time.now(), task_number=task_number)
            request = TaskStatus(status=TaskStatus.END)
            response = end(task_id, request)
        except (rospy.ServiceException, rospy.ROSException), e:
            rospy.logerr("Service call failed: {}".format(e))

    def load_test_events(self, file_name):
        self.test_events = deque()
        data_file = file_name
        try:
            rospy.loginfo("Loading data from {}".format(file_name))
            with open(data_file) as csvfile:
                data = csv.reader(csvfile, delimiter='\t', quotechar='|')
                self.start_datetime = None
                for row in data:
                    rospy.loginfo(row[0])
                    if len(row) == 0:
                        break
                    dt = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S.%f")
                    if self.start_datetime is None:
                        self.start_datetime = dt
                    time_diff = (dt - self.start_datetime)
                    time_diff = (time_diff.seconds * 1000000) + time_diff.microseconds
                    if len(row) > 4:
                        self.test_events.append((row[1], row[2], row[3], row[4], dt, time_diff))
                    else:
                        self.test_events.append((row[1], row[2], dt, time_diff))
            rospy.loginfo("{} loaded successfully with total_events={}".format(file_name, len(self.test_events)))
            return True
        except IOError as e:
            rospy.logerr("I/O error({0}): {1}".format(e.errno, e.strerror))
        return False

    def test_task_controller(self, request):
        response = TaskStatus(
            status=TaskStatus.SUCCESS,
            text='SUCCESS')
        if request.id.task_number < Task.size:
            if self.task_number is None \
               and request.request.status == TaskStatus.START \
               and self.task_status.status == TaskStatus.PENDING:
                success = self.load_test_events(request.file)
                if success and len(self.test_events) > 0:
                    self.current_event = self.test_events.popleft()
                    self.start_task(task_number=request.id.task_number)
                    self.task_number = request.id.task_number
                    self.pause = False
                    self.task_status.status = TaskStatus.ACTIVE
                    self.task_status.text = "ACTIVE"
                    rospy.loginfo("{}: START".format(Task.types[self.task_number]))
                    return TestTaskControllerResponse(response)
            elif self.task_number == request.id.task_number \
               and request.request.status == TaskStatus.END \
               and self.task_status.status == TaskStatus.ACTIVE:
                self.end_task(task_number=request.id.task_number)
                self.task_number = None
                self.pause = False
                self.task_status.status = TaskStatus.PENDING
                self.task_status.text = "PENDING"
                rospy.loginfo("{}: END".format(Task.types[request.id.task_number]))
                return TestTaskControllerResponse(response)

        rospy.logwarn("Invalid task request")
        response.status = TaskStatus.FAILED
        response.text = "FAILED"
        return TestTaskControllerResponse(response)

    def pause_dummy_publish(self, request):
        self.pause = request.pause
        rospy.logwarn("Publish dummy pause: {}".format(self.pause))
        return PauseResponse(True)

    def casas_publish_event(self):
        while True:
            while self.task_status.status == TaskStatus.ACTIVE:
                while self.pause:
                    time.sleep(.5)

                epoch = time.mktime(self.current_event[-2].timetuple()) \
                            + self.current_event[-2].microsecond * 1e-6
                new_event = objects.Event(
                    category='test',
                    package_type='test',
                    sensor_type='test',
                    message=self.current_event[1],
                    target=self.current_event[0],
                    serial=self.mac_address,
                    by='ROS_Node_'+rospy.get_name()[1:],
                    channel='rawevents',
                    site='test',
                    epoch='{:f}'.format(epoch),
                    uuid=uuid.uuid4().hex)
                #rospy.loginfo(new_event.get_json())
                self.rcon.publish_to_exchange(
                    exchange_name='test.events.testbed.casas',
                    casas_object=new_event)

                if len(self.test_events) == 0:
                    self.end_task(task_number=self.task_number)
                    rospy.loginfo("No more events in file")
                    rospy.loginfo("{}: END".format(Task.types[self.task_number]))
                    self.task_number = None
                    self.pause = False
                    self.task_status.status = TaskStatus.PENDING
                    self.task_status.text = "PENDING"
                    break

                next_event = self.test_events.popleft()
                pause_time = (next_event[-1] - self.current_event[-1]) * 1e-06
                rospy.loginfo("num event left={} pause time={}".format(len(self.test_events), pause_time))
                self.current_event = next_event
                time.sleep(pause_time * self.speed)

            time.sleep(.5)

    def casas_run(self):
        try:
            self.rcon.run()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        if self.task_status.status == TaskStatus.ACTIVE:
            self.task_status.status = TaskStatus.PENDING
            self.end_task()
            rospy.loginfo("{}: END".format(Task.types[self.task_number]))
        rospy.loginfo("Disconnecting casas connection")
        self.rcon.stop()

if __name__ == "__main__":
    rospy.init_node("test_error_detector", disable_signals=True)
    if len(sys.argv) < 2:
        ted = TestErrorDetector(speed=1)
    else:
        ted = TestErrorDetector(speed=float(sys.argv[1]))
    ted.casas_run()
    rospy.on_shutdown(ted.stop)
