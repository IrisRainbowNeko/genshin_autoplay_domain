import time

import numpy as np

from utils import *

class AwardController:
    def __init__(self, capture):
        self.capture=capture

        self.lsd = cv2.createLineSegmentDetector(0)
        self.dmove=500/33.2
        self.t_mid=3.9
        self.t_goal=20
        self.award_thr=0.85
        self.cc=0

        self.dir_area = [168 - 26, 125 - 26, 168 + 26, 125 + 26]
        self.award_area = [1089, 507, 1089 + 121, 507 + 64]
        self.resin_area = [572, 727, 572 + 58, 727 + 61]

        self.pos_resin_double = [664, 759]
        self.pos_over = [675, 1000]

        self.start_temp = cv2.imread('imgs/start_temp.png')
        self.start_mask = cv2.imread('imgs/start_mask.png', cv2.IMREAD_GRAYSCALE)

        self.award_temp = cv2.imread('imgs/award_temp.png')
        self.award_mask = cv2.imread('imgs/award_mask.png', cv2.IMREAD_GRAYSCALE)

        self.resin_temp = cv2.imread('imgs/resin_temp.png')

    def pre_proc(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        low_hsv = np.array([80, 130, 200])
        high_hsv = np.array([100, 255, 255])
        mask = cv2.inRange(hsv, lowerb=low_hsv, upperb=high_hsv)
        return mask

    def find_close(self, line1, line2, thr=10):
        if np.linalg.norm(line1[0:2] - line2[0:2]) < thr:
            return 0, 0
        elif np.linalg.norm(line1[0:2] - line2[2:4]) < thr:
            return 0, 2
        elif np.linalg.norm(line1[2:4] - line2[2:4]) < thr:
            return 2, 2
        elif np.linalg.norm(line1[2:4] - line2[0:2]) < thr:
            return 2, 0
        else:
            return None

    def filter_line_group(self, lines, angle_t=57, angle_thr=5):
        flines = []
        for i, line1 in enumerate(lines):
            for line2 in lines[i + 1:]:
                res = self.find_close(line1, line2)

                if res is None:
                    continue
                i1, i2 = res
                v1 = line1[i1 ^ 2:(i1 ^ 2) + 2] - line1[i1:i1 + 2]
                v2 = line2[i2 ^ 2:(i2 ^ 2) + 2] - line2[i2:i2 + 2]
                angle = np.arccos((np.dot(v1, v2)) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
                angle = np.rad2deg(angle)

                if abs(angle - angle_t) < angle_thr:
                    flines.append(v1)
                    flines.append(v2)
        return flines

    def cal_dir(self, vecs):
        if len(vecs) < 2:
            return None
        vc = (vecs[0] + vecs[1]) / 2
        angle = np.rad2deg(np.arctan2(-vc[1], -vc[0]))
        return angle

    def filter_line(self, lines, thr_len=18):
        res = []
        for dline in lines:
            if (dline[2] - dline[0]) ** 2 + (dline[3] - dline[1]) ** 2 < thr_len ** 2:
                continue
            res.append(dline)
        return res

    def get_dir(self):
        patch = self.capture.cap_box(self.dir_area)
        gray = self.pre_proc(patch)
        self.gray=gray
        dlines = self.lsd.detect(gray)[0]
        if dlines is None:
            return None
        dlines = [x[0] for x in dlines]
        dlines = self.filter_line(dlines)
        dlines = self.filter_line_group(dlines)

        actor_angle = self.cal_dir(dlines)
        return actor_angle

    def dir_to(self, angle, thr=3, record=False):
        while True:
            actor_angle = self.get_dir()
            if actor_angle is None:
                tap_key(87, 0.1)
                time.sleep(0.3)
                continue
            mouse_ctrl.move_steps((angle - actor_angle) * self.dmove, 0, n=10, t=1)
            break
        while True:
            tap_key(87, 0.1)
            time.sleep(0.3)
            actor_angle = self.get_dir()
            if actor_angle is None:
                #cv2.imwrite(f'tmp/{self.cc}.png', self.gray)
                self.cc+=1
                if record:
                    self.retry+=0.05
                continue
            if abs(actor_angle-angle)<thr:
                break
            #print(abs(actor_angle-angle))
            mouse_ctrl.move(int(10*(angle-actor_angle)), 0)

    def to_award(self):
        press_key(87)
        while True:
            patch = self.capture.cap_box(box=self.award_area)
            mv = match_img(patch, self.award_temp, cv2.TM_CCOEFF_NORMED, mask=self.award_mask)
            if mv[-1]>self.award_thr:
                break
        release_key(87)

    def move(self):
        self.retry=0

        tap_key(87, 0.1)
        time.sleep(0.3)

        self.dir_to(-90)
        tap_key(87, 10)

        self.dir_to(90)
        tap_key(87, self.t_mid-self.retry)

        self.dir_to(0)
        tap_key(87, 5)
        self.dir_to(0) #中间可能有东西
        self.to_award()

        time.sleep(0.3)
        tap_key(ord('F'), 0.1)

        time.sleep(1.0)
        sc=psnr(self.capture.cap_box(box=self.resin_area), self.resin_temp)
        #print(sc)
        if sc>20:
            mouse_ctrl.click(self.pos_resin_double)

        time.sleep(10)
        mouse_ctrl.click(self.pos_over)


    def move_start(self):
        press_key(87)
        while True:
            patch = self.capture.cap_box(box=self.award_area)
            mv = match_img(patch, self.start_temp, cv2.TM_CCOEFF_NORMED, mask=self.start_mask)
            if mv[-1] > self.award_thr:
                break
        release_key(87)