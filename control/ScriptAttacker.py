import os
import random

import cv2
import sys

from utils import *
import time
import yaml

class ScriptAttacker:
    def __init__(self, capture, screen_size=(1920, 1080)):
        self.capture=capture

        self.screen_size=screen_size
        self.screen_center = (screen_size[0] // 2, screen_size[1] // 2)
        #self.ratio=(screen_size[0]/2560, screen_size[1]/1440)

        self.switch_range = [1730, 215, 1760, 615]
        self.ratio = screen_size[0]/1920

        self.switch_temp = cv2.imread('imgs/switch_temp.png')
        self.switch_mask = cv2.imread('imgs/switch_mask.png', cv2.IMREAD_GRAYSCALE)

        self.scripts={'normal':{}, 'break':{}}
        self.actor_now='1'
        self.move_list=[ord(x) for x in ['W','A','S','D']]

    def load_script(self, file):
        for v in self.scripts.values():
            v.clear()

        with open(file, encoding='utf8') as f:
            data = yaml.load(f.read(), Loader=yaml.FullLoader)

        for name, item in data.items():
            item['action']=[x.split() for x in item['action'].split('\n') if not (x.startswith('#') or len(x)<=0)]
            item['timer']=0

            if 'type' in item:
                self.scripts[item['type']][name]=item
            else:
                self.scripts['normal'][name] = item

        #self.scripts=data

    def switch_actor(self, a_id: str):
        self.actor_now=a_id
        for i in range(15):
            if i>=2:
                tap_key(random.choice(self.move_list), 0.2)

            tap_key(ord(a_id), 0.1)
            cap_area=[*self.switch_range[:2], self.switch_range[2]-self.switch_range[0], self.switch_range[3]-self.switch_range[1]]
            img=self.capture.cap(area=[int(x*self.ratio) for x in cap_area], resize=tuple(cap_area[2:]))
            y=match_img(img, self.switch_temp, cv2.TM_CCOEFF_NORMED, mask=self.switch_mask)[5]
            #print(f'switch:{a_id}, times:{i}, now:{y//85+1}')
            if y//95==int(a_id)-1:
                return
            time.sleep(0.3)

    def attack(self, plan, open_break=True):
        mouse_dict={'r':MOUSE_RIGHT, 'l':MOUSE_LEFT}

        for cmd in plan:
            if win32api.GetKeyState(ord('P')) < 0:
                sys.exit(0)
                return

            if open_break:
                #a_id = self.actor_now
                self.step_break()
                #self.switch_actor(a_id)

            if cmd[0]=='key':
                if len(cmd)==2:
                    tap_key(ord(cmd[1].upper()), 0.1)
                else:
                    (press_key if cmd[1]=='down' else release_key)(ord(cmd[2].upper()))
            elif cmd[0]=='mouse':
                button=mouse_dict[cmd[1]]
                mouse_ctrl.down(button)
                time.sleep(float(cmd[2]))
                mouse_ctrl.up(button)
            elif cmd[0]=='delay':
                time.sleep(float(cmd[1]))
            elif cmd[0]=='switch':
                self.switch_actor(cmd[1])
            else:
                raise ValueError("unknown cmd")

    def step_break(self):
        for name, item in self.scripts['break'].items():
            if time.time() - item['timer'] >= item['interval']:
                item['timer'] = time.time()
                self.attack(item['action'], open_break=False)
                return True
        return False

    def step(self):
        for name, item in self.scripts['normal'].items():
            if time.time()-item['timer']>=item['interval']:
                item['timer'] = time.time()
                self.attack(item['action'])
                break