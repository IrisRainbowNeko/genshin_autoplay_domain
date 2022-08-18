from mmtracking.Interface import TrackerInterface
from yolox.Interface import DetectorInterface
from yolox.exp import get_exp

import argparse
import win32api
import winsound
import time
import yaml
import sys

from yolox.Interface import GENSHIN_CLASSES
from window_capture import WindowCapture
from control import *
from utils import *

class AutoPlayer:
    def __init__(self, args):
        self.args=args
        exp = get_exp(args.yolox_exp_file, None)
        self.detector = DetectorInterface(exp)
        self.tracker = TrackerInterface()

        self.pred_imsize = (1280, 720)

        self.capture = WindowCapture('原神')
        self.controller = FollowController(self.pred_imsize)
        self.attacker = ScriptAttacker(self.capture)

        self.enemy_selector=ConfSelector()

        self.award_c1=AwardController(self.capture)
        self.domain_selector=DomainSelector(self.capture)

        self.pred_ratio = self.capture.DEFAULT_MONITOR_WIDTH/self.pred_imsize[0]

        self.return_temp = cv2.imread('imgs/return_temp.png')

        self.finish_temp = cv2.imread('imgs/finish_temp.png')
        self.finish_mask = cv2.imread('imgs/finish_mask.png', cv2.IMREAD_GRAYSCALE)
        self.finish_area = [929, 945, 929+140, 945+28]
        self.finish_temp_b = self.pre_proc(self.finish_temp)

        self.team_temp = cv2.imread('imgs/team_temp.png')
        self.team_area = [888, 36, 888 + 144, 36 + 24]
        self.team_dw = 36
        self.pos_team_l = [77, 540]
        self.pos_team_r = [1840, 540]
        self.pos_team_sel = [1646, 1016]

        self.lost_count=0

    def set_border_offset(self):
        tap_key(27, 0.2) #ESC
        time.sleep(1)

        img = self.capture.cap()[:200,:200,:]
        info = match_img(img, self.return_temp)
        print('offset:', info[0]-19, info[1]-19)
        print('G offset:', info[0]-19+self.capture.genshin_window_rect[0], info[1]-19+self.capture.genshin_window_rect[1])
        self.capture.set_offset(info[0]-19, info[1]-19)
        mouse_ctrl.set_offset(info[0]-19+self.capture.genshin_window_rect[0], info[1]-19+self.capture.genshin_window_rect[1])

        tap_key(27, 0.2)  # ESC
        time.sleep(0.6)

    def check_enemy(self, bboxes):
        if bboxes is None:
            mouse_ctrl.move(150, 0)
            return False

        max_conf = bboxes[:,5].max()

        if max_conf<self.detector.exp.test_conf:
            mouse_ctrl.move(150, 0)
            return False
        else:
            return True

    def pre_proc(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        low_hsv = np.array([20, 200, 230])
        high_hsv = np.array([25, 255, 255])
        mask = cv2.inRange(hsv, lowerb=low_hsv, upperb=high_hsv)
        return mask

    def check_finish(self, img):
        #img = self.capture.cap(area=self.finish_area, resize=(self.finish_area[0]/self.pred_ratio, self.finish_area[1]/self.pred_ratio))
        binary = self.pre_proc(img)
        score = match_img(binary, self.finish_temp_b, cv2.TM_CCOEFF_NORMED, mask=None)[-1]
        #print('sc:', score)
        return score>0.39

    def tatakai(self):
        while True:
            self.det_re=0
            while True:
                if win32api.GetKeyState(ord('P')) < 0:
                    sys.exit(0)
                    return

                img = self.capture.cap()

                img_cf = clip_img(img, self.finish_area)
                if self.check_finish(img_cf):
                    return

                img = cv2.resize(img, self.pred_imsize)

                bboxes = self.detector.predict(img)
                #print(bboxes)
                if self.check_enemy(bboxes): #没检测到怪就重试
                    break
                self.det_re+=1
                if self.det_re>=self.args.max_retry:
                    break
            if self.det_re >= self.args.max_retry:
                self.attacker.step()
                break

            bbox = self.enemy_selector.select(bboxes)
            enemy = GENSHIN_CLASSES[int(bbox[4])]
            recoder.write(f'{int(time.time() * 1000) - time_start}, {bbox.tolist()}, {enemy}\n')

            self.lost_count=0
            self.tracker.reset(bbox[:4])

            time_track_start=time.time()

            self.controller.reset()
            while True: #进入追踪阶段
                if win32api.GetKeyState(ord('P')) < 0:
                    sys.exit(0)
                    return

                if self.controller.step(bbox[:4], enemy):  # 追踪目标执行完毕
                    self.attacker.step()  # 按预设进行攻击
                    break

                img = self.capture.cap(resize=self.pred_imsize)
                bbox = self.tracker.predict(img)
                #print(bbox[-1])
                if time.time()-time_track_start>self.args.track_timeout:
                    break
                if bbox[4]<self.args.lost_score:
                    self.lost_count+=1
                    if self.lost_count>=self.args.lost_times:
                        break

    def switch_team(self, tid):
        tap_key(ord('L'), 0.1)
        time.sleep(5)

        patch = self.capture.cap_box(box=self.team_area)
        x = match_img(patch, self.team_temp)[4]
        now_tid = x//36
        print(now_tid)

        if now_tid<tid:
            for _ in range(tid-now_tid):
                mouse_ctrl.click(self.pos_team_r)
                time.sleep(0.3)
        else:
            for _ in range(now_tid-tid):
                mouse_ctrl.click(self.pos_team_l)
                time.sleep(0.3)

        mouse_ctrl.click(self.pos_team_sel)
        time.sleep(0.3)

        tap_key(27, 0.1)
        time.sleep(3)

    def load_cfg(self, path):
        with open(path, encoding='utf8') as f:
            data = yaml.load(f.read(), Loader=yaml.FullLoader)

        self.domain_list=data

    def step(self, cfg):
        self.switch_team(cfg['team']-1)

        self.domain_selector.moveto(cfg['秘境'][0], int(cfg['秘境'][1])-1)
        time.sleep(0.5)

        self.attacker.load_script(f'control/script/{cfg["策略"]}.yaml')
        #self.attacker.load_script('control/script/hutao_shatang.yaml')

        self.award_c1.move_start()
        time.sleep(0.3)
        tap_key(ord('F'), 0.1)
        time.sleep(0.8)

        print('ttk start')
        self.tatakai()
        print('ttk ok')
        self.award_c1.move()
        time.sleep(10)

    def start(self):
        self.load_cfg(self.args.cfg)
        for item in self.domain_list:
            self.step(item)

def get_args():
    parser = argparse.ArgumentParser("Genshin Auto Domain")
    parser.add_argument("--yolox_exp_file", type=str, default='yolox/exp/yolox_s_genshin.py')
    parser.add_argument("--lost_score", type=float, default=0.6)
    parser.add_argument("--lost_times", type=int, default=4)
    parser.add_argument("--track_timeout", type=float, default=4.5)
    parser.add_argument("--max_retry", type=int, default=200)

    parser.add_argument("--cfg", type=str, default='cfgs/p1.yaml')

    return parser.parse_args()

if __name__ == '__main__':
    args=get_args()
    player = AutoPlayer(args)

    print('press t to start')
    winsound.Beep(700, 500)
    time_start = int(time.time() * 1000)
    recoder = open('log.txt', 'w', encoding='utf8')
    while win32api.GetKeyState(ord('T')) >= 0:
        pass

    player.set_border_offset()
    player.start()
    print('finish')
    recoder.close()