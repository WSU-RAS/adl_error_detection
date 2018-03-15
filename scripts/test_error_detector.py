#!/usr/bin/env python

import rospy
import rospkg
import datetime
import logging
import configparser
import csv
import uuid
import time

from collections import defaultdict
from adl.util import ConnectPythonLoggingToRos
from adl.util import Task
from casas import objects, rabbitmq

from ras_msgs.msg import TaskStatus, TaskId
from ras_msgs.srv import TestTaskController, TestTaskControllerResponse
from ras_msgs.srv import TaskController

class TestErrorDetector:

    def __init__(self):
        rospy.loginfo("Initializing Test Error Detector")

        rospack = rospkg.RosPack()
        self.pkg_path = rospack.get_path('adl_error_detection')

        self.task_number = None
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
            amqp_host=default['AmqpHost'],
            amqp_port=default['AmqpPort'],
            amqp_vhost=default['AmqpVHost'],
            amqp_ssl=default.getboolean('AmqpSSL'),
            translations=self.translate)
        self.rcon.l.addHandler(ConnectPythonLoggingToRos())
        self.rcon.set_on_connect_callback(self.casas_on_connect)

    def casas_on_connect(self):
        self.ros_setup()
        self.rcon.call_later(1, self.casas_publish_event)

    def ros_setup(self):
        # start task rosservice server
        self.task_service = rospy.Service(
            'test_task_controller', TestTaskController,
            self.test_task_controller)
        rospy.loginfo("test_task_controller service running")

    def start_task(self, task_number=None):
        rospy.wait_for_service("task_controller")
        try:
            start = rospy.ServiceProxy('task_controller', TaskController)
            task_id = TaskId(stamp=rospy.Time.now(), task_number=task_number)
            request = TaskStatus(status=TaskStatus.START)
            response = start(task_id, request)
        except rospy.ServiceException, e:
            rospy.logerr("Service call failed: {}".format(e))

    def end_task(self, task_number=None):
        rospy.wait_for_service("task_controller")
        try:
            end = rospy.ServiceProxy('task_controller', TaskController)
            task_id = TaskId(stamp=rospy.Time.now(), task_number=task_number)
            request = TaskStatus(status=TaskStatus.END)
            response = end(task_id, request)
        except rospy.ServiceException, e:
            rospy.logerr("Service call failed: {}".format(e))

    def load_test_events(self, file_name):
        self.test_event_index = 0
        self.test_events_ctr = 0
        self.test_events = defaultdict(list)
        data_file = self.pkg_path + "/data/" + file_name
        rospy.loginfo("Loading data from {}".format(file_name))
        with open(data_file) as csvfile:
            data = csv.reader(csvfile, delimiter=' ', quotechar='|')
            self.start_datetime = None
            for row in data:
                if len(row) == 0:
                    break
                dt = datetime.datetime.strptime(row[0] + ' ' + row[1], "%Y-%m-%d %H:%M:%S")
                if self.start_datetime is None:
                    self.start_datetime = dt
                time_diff = (dt - self.start_datetime).total_seconds()
                status = True if row[3] == 'start' else False
                if len(row) > 4:
                    self.test_events[int(time_diff)].append(
                        (row[2], status, row[4], True if row[5] == 'start' else False))
                else:
                    self.test_events[int(time_diff)].append((row[2], status))
        rospy.loginfo("{} loaded successfully with total_events={}".format(file_name, len(self.test_events)))
        self.test_events_len = len(self.test_events)
        
    def test_task_controller(self, request):
        response = TaskStatus(
            status=TaskStatus.SUCCESS,
            text='SUCCESS')
        if request.id.task_number < Task.size:
            if self.task_number is None \
               and request.request.status == TaskStatus.START \
               and self.task_status.status == TaskStatus.PENDING:
                self.load_test_events(request.file)
                self.start_task(task_number=request.id.task_number)
                self.task_number = request.id.task_number
                self.task_status.status = TaskStatus.ACTIVE
                self.task_status.text = "ACTIVE"
                rospy.loginfo("{}: START".format(Task.types[self.task_number]))
                return TestTaskControllerResponse(response)
            elif self.task_number == request.id.task_number \
               and request.request.status == TaskStatus.END \
               and self.task_status.status == TaskStatus.ACTIVE:
                self.end_task(task_number=request.id.task_number)
                self.task_number = None
                self.task_status.status = TaskStatus.PENDING
                self.task_status.text = "PENDING"
                rospy.loginfo("{}: END".format(Task.types[request.id.task_number]))
                return TestTaskControllerResponse(response)

        rospy.logwarn("Invalid task request")
        response.status = TaskStatus.FAILED
        response.text = "FAILED"
        return TestTaskControllerResponse(response)

    def casas_publish_event(self):
        if self.task_status.status == TaskStatus.ACTIVE:
            if self.test_events_ctr == self.test_events_len:
                self.end_task(task_number=self.task_number)
                rospy.loginfo("No more events in file")
                rospy.loginfo("{}: END".format(Task.types[self.task_number]))
                self.task_number = None
                self.task_status.status = TaskStatus.PENDING
                self.task_status.text = "PENDING"
                self.rcon.call_later(1, self.casas_publish_event)
                return

            if self.test_event_index in self.test_events:
                self.test_events_ctr += 1
                rospy.loginfo("ctr={} total={}".format(self.test_events_ctr, self.test_events_len))

            epoch = time.mktime(datetime.datetime.now().timetuple()) \
                + datetime.datetime.now().microsecond * 1e-6

            for event in self.test_events[self.test_event_index]:
                new_event = objects.Event(
                    category='entity',
                    package_type='Estimote-Sticker',
                    sensor_type='Estimote-Movement',
                    message='MOVED' if event[1] else 'STILL',
                    target=event[0],
                    serial='5c02cb086ce7',
                    by='EstimoteAgent',
                    channel='rawevents',
                    site='kyoto',
                    epoch='{:f}'.format(epoch),
                    uuid=str(uuid.uuid4()).replace('-', ''))
                #rospy.loginfo(new_event.get_json())
                self.rcon.publish_to_exchange(
                    exchange_name='test.events.testbed.casas',
                    casas_object=new_event)

            self.test_event_index += 1
        self.rcon.call_later(1, self.casas_publish_event)

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
    ted = TestErrorDetector()
    ted.casas_run()
    rospy.on_shutdown(ted.stop)