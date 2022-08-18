import time

import numpy as np

from utils import *

class FollowController:
    def __init__(self, imsize, th_center=0.11, th_close=0.593, th_close_syfs=0.55, th_close_size=0.22, base_move_speed=150, screen_size=(1920, 1080)):
        self.imsize=imsize
        self.im_center=(imsize[0]//2, imsize[1]//2)
        self.th_center=th_center
        self.th_close_size=th_close_size
        self.th_close=th_close
        self.th_close_syfs=th_close_syfs
        self.screen_size=screen_size
        self.screen_center=(screen_size[0]//2, screen_size[1]//2)
        self.base_move_speed=base_move_speed

        self.go=False
        self.key_go=87

        self.rot_st=0
        self.rot_timeout=2

    def step(self, bbox, enemy):
        cx=(bbox[0]+bbox[2])/2
        #cy=(bbox[1]+bbox[3])/2
        #h=bbox[3]-bbox[1]
        dx_rate=(cx-self.im_center[0])/self.imsize[0]
        dx_rate=np.sign(dx_rate)*0.1 if abs(dx_rate)<0.1 else dx_rate

        if self.is_close(bbox, enemy) and abs(dx_rate)<=self.th_center:
            if self.go:
                release_key(self.key_go)
                release_key(16)
            return True
        else:
            if self.move_player(dx_rate):
                return False
            else:
                return True

    def reset(self):
        self.rot_st=time.time()

    def is_close(self, bbox, enemy):
        close=False
        if bbox[3]/self.imsize[1] >= self.th_close:
            close=True

        if enemy.find('深渊法师')!=-1 and (bbox[3]/self.imsize[1] >= self.th_close_syfs or (bbox[3]-bbox[1])/self.imsize[1] >= self.th_close_size):
            close = True

        return close

    def move_player(self, dx_rate):
        if abs(dx_rate)>self.th_center:
            if self.go:
                release_key(self.key_go)
                release_key(16)
            if time.time()-self.rot_st>self.rot_timeout:
                return False

            #mouse_down(*self.screen_center)
            mvdx=int(self.base_move_speed*dx_rate*2)
            mouse_ctrl.move(mvdx, 0)
            #mouse_up(self.screen_center[0]+mvdx, self.screen_center[1])
        else:
            press_key(self.key_go)
            press_key(16)
            self.go=True

        return True