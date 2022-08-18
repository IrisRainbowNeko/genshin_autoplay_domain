import time

import numpy as np

from utils import *

class DomainSelector:
    def __init__(self, capture):
        self.capture=capture

        self.pos_area_choose=(1920-65, 1080-65)
        self.pos_ts=(1613, 1016)
        self.pos_small=(28, 652)

        self.pos_area = {
            '蒙德': (1627, 120),
            '璃月': (1627, 220),
            '稻妻': (1627, 320),
        }

        self.pos_domain={
            '火': [(58,50), self.move_huo, cv2.imread('imgs/domain_huo.png'), (1627, 120)],
            '千岩': [(57,57), self.move_normal, cv2.imread('imgs/domain_qianyan.png'), (1627, 120)],
            '风': [(61,28), self.move_normal, cv2.imread('imgs/domain_feng.png'), (1627, 120)],
            '冰': [(54,31), self.move_bing, cv2.imread('imgs/domain_bing.png'), (1627, 120)],
            '宗室': [(37,43), self.move_normal, cv2.imread('imgs/domain_zongshi.png'), (1627, 120)],
            '雷': [(28,49), self.move_normal, cv2.imread('imgs/domain_lei.png'), (1627, 120)],

            '辰砂': [(35,31), self.move_normal, cv2.imread('imgs/domain_chensha.png'), (1627, 230)],
            '岩': [(44,46), self.move_normal, cv2.imread('imgs/domain_yan.png'), (1627, 230)],

            '绝缘': [(34,30), self.move_normal, cv2.imread('imgs/domain_jueyuan.png'), (1627, 340)],
            '华馆': [(47,54), self.move_normal, cv2.imread('imgs/domain_huaguan.png'), (1627, 340)],
        }

        self.idx_1=(212, 176)
        self.idx_dy=107

        self.pos_enter=(1650, 1015)

        self.dst_area=[847,415,847+136,415+39]

        self.dst_temp=cv2.imread('imgs/dst_temp.png')

    def moveto(self, name, idx):
        tap_key(ord('M'), 0.2)
        time.sleep(0.5)

        mouse_ctrl.click(self.pos_area_choose)

        mouse_ctrl.click(self.pos_domain[name][3])
        time.sleep(0.8)

        for i in range(5):
            mouse_ctrl.click(self.pos_small)
            time.sleep(0.1)

        dpos = match_img(self.capture.cap(), self.pos_domain[name][2])[:2]
        mouse_ctrl.click(np.array(self.pos_domain[name][0])+np.array(dpos))
        time.sleep(0.2)
        mouse_ctrl.click(self.pos_ts)
        time.sleep(5)

        self.pos_domain[name][1]()

        mouse_ctrl.click((self.idx_1[0], self.idx_1[1]+self.idx_dy*idx))
        time.sleep(0.8)
        mouse_ctrl.click(self.pos_enter)
        time.sleep(2)
        mouse_ctrl.click(self.pos_enter)
        time.sleep(2)
        wait_for_img(self.dst_temp, lambda :self.capture.cap_box(box=self.dst_area), thr=14)
        time.sleep(2)
        mouse_ctrl.click(self.pos_enter)

    def move_normal(self):
        tap_key(87, 2)
        time.sleep(0.3)
        tap_key(ord('F'), 0.2)
        time.sleep(4)

    def move_huo(self):
        mouse_ctrl.move_steps(-80 * (500 / 33.2), 0, n=10, t=1)
        self.move_normal()

    def move_bing(self):
        tap_key(ord('F'), 0.2)
        time.sleep(4)