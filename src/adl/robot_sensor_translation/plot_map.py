#!/usr/bin/env python

import rospy
import cv2
import numpy as np
import threading
import Queue

class RobotXYViz(object):

    sensors = [
        (76, 64), #M004
        (201, 59), #M005
        (322, 60), #M011
        (443 ,61), #M012
        (76, 191), #M003
        (201, 182), #M006
        (316, 188), #M010
        (448, 183), #M013
        (75, 303), #M002
        (199, 302), #M007
        (321, 304), #M009
        (443, 308), #M014

        (273, 365), #M008
        (151, 417), #M001
        (409, 418), #M015

        (152, 447), #M023
        (175, 483), #M060
        (175, 543), #M059
        (156, 583), #M022
        (175, 604), #M058
        (175, 666), #M057
        (157, 721), #M021
        (176, 729), #M056
        (176, 789), #M055
        (156, 824), #M024
        (176, 851), #M054
        (43, 836), #M025

        (406, 446), #M016
        (409, 603), #M017
        (409, 721), #M018
        (280, 718), #M019
        (272, 798), #M020
        (398, 830), #M051
    ]

    def __init__(self, height=1000, width=600, scale=0.5, name='kyoto', visible=True):
        self.name = name
        self.points = Queue.Queue()
        self.__visible = visible
        self.reset()
        threading.Thread(target=self._plot).start()

    def reset(self):
        self.points.queue.clear()
        # self.__visible = False
        self.__img = np.ones((1000, 600, 3), np.uint8) * 255
        self.__last_point = None
        cv2.rectangle(self.__img, (0,0), (522,895), (255,0,0), 1) # outer outline
        cv2.rectangle(self.__img, (0, 425), (99,780), (255,0,0), 1) # stairs
        cv2.rectangle(self.__img, (204,425), (354,667), (255,0,0), 1) # hallway closet/kitchen left
        cv2.rectangle(self.__img, (206,762), (348,895), (255,0,0), 1) # pantry
        cv2.rectangle(self.__img, (452,425), (522,895), (255,0,0), 1) # kitchen right

        # sensors
        for s_point in self.sensors:
            cv2.circle(self.__img, s_point, 5, (120,120,120), 2)

    def view_plot(self, visible=True):
        if not visible and self.__visible:
            cv2.destroyWindow('RobotXYViz-{}'.format(self.name))
        self.__visible = visible

    def _plot(self):
        while True:
            if not self.points.empty():
                new_point = self.points.get()
                self.__img[896:1000, 0:600] = [255, 255, 255]
                xy_str = '({0:.3f}, {1:.3f})'.format(new_point[0], new_point[1])
                cv2.putText(self.__img, xy_str, (10,930),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1)
                if self.__last_point != None:
                    cv2.arrowedLine(
                        self.__img,
                        (int(self.__last_point[0] * 100), int(self.__last_point[1] * 100)),
                        (int(new_point[0] * 100), int(new_point[1] * 100)),
                        (0, 0, 255), thickness=1, line_type=cv2.LINE_AA, tipLength=0.15)
                self.__last_point = new_point
            small_img = cv2.resize(self.__img, None, fx=0.5, fy=0.5)
            if self.__visible:
                cv2.imshow('RobotXYViz-{}'.format(self.name), small_img)

            k = cv2.waitKey(1)
            if k in [27, ord('q')]:
                self.view_plot(visible=False)
                rospy.signal_shutdown("User request")
                break

    def add_point(self, x, y):
        self.points.put((y, x)) # Purposely swap x,y since we rotated map

    def save_image(self, file_name):
        if self.__last_point is not None:
            cv2.imwrite(file_name, self.__img)
