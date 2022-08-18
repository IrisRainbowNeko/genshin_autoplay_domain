import win32api, win32con
import time
import cv2
import numpy as np

import ctypes
awareness = ctypes.c_int()
ctypes.windll.shcore.SetProcessDpiAwareness(2)

MOUSE_LEFT=0
MOUSE_MID=1
MOUSE_RIGHT=2
mouse_list_down=[win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_RIGHTDOWN]
mouse_list_up=[win32con.MOUSEEVENTF_LEFTUP, win32con.MOUSEEVENTF_MIDDLEUP, win32con.MOUSEEVENTF_RIGHTUP]

from win32api import GetSystemMetrics

print("Screen Width =", GetSystemMetrics(0))
print("Screen Height =", GetSystemMetrics(1))

def mouse_down(x, y, button=MOUSE_LEFT):
    time.sleep(0.02)
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(mouse_list_down[button], 0, 0, 0, 0)

def mouse_move(dx, dy):
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)

def mouse_up(x, y, button=MOUSE_LEFT):
    time.sleep(0.02)
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(mouse_list_up[button], 0, 0, 0, 0)

def mouse_click(x, y, button=MOUSE_LEFT):
    mouse_down(x, y, button)
    mouse_up(x, y, button)

def release_key(key_code):
    win32api.keybd_event(key_code, win32api.MapVirtualKey(key_code, 0), win32con.KEYEVENTF_KEYUP, 0)

def press_key(key_code):
    win32api.keybd_event(key_code, win32api.MapVirtualKey(key_code, 0), 0, 0)

def tap_key(key_code, t):
    press_key(key_code)
    time.sleep(t)
    release_key(key_code)

class MouseController:
    def __init__(self, sx, sy):
        self.px=sx
        self.py=sy

        self.ofx = 0
        self.ofy = 0

    def set_offset(self, ofx, ofy):
        self.ofx = ofx
        self.ofy = ofy

    def move(self, dx, dy):
        mouse_move(dx, dy)
        self.px+=dx
        self.py+=dy

    def move_steps(self, dx, dy, n=10, t=1):
        idx = dx/n
        idy = dy/n
        dt = t/n

        for i in range(n):
            self.move(int(idx), int(idy))
            time.sleep(dt)

    def down(self, button=MOUSE_LEFT, pos=None):
        if pos is None:
            mouse_down(self.px, self.py, button)
        else:
            mouse_down(pos[0]+self.ofx, pos[1]+self.ofy, button)

    def up(self, button=MOUSE_LEFT, pos=None):
        if pos is None:
            mouse_up(self.px, self.py, button)
        else:
            mouse_up(pos[0]+self.ofx, pos[1]+self.ofy, button)

    def click(self, pos=None, t=0.1):
        self.down(pos=pos)
        time.sleep(t)
        self.up(pos=pos)

mouse_ctrl = MouseController(2560//2, 1440//2)

ch_int_dict={'一':1, '二':2, '三':3, '四':4, '五':5, '六':6, '七':7, '八':8, '九':9, }
def trans_ch_int(text):
    if text in ch_int_dict:
        return ch_int_dict[text]
    else:
        return 1

def match_img(img, target, type=cv2.TM_CCOEFF_NORMED, mask=None):
    h, w = target.shape[:2]
    res = cv2.matchTemplate(img, target, type, mask=mask)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if type in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        return (
            *min_loc,
            min_loc[0] + w,
            min_loc[1] + h,
            min_loc[0] + w // 2,
            min_loc[1] + h // 2,
            min_val,
        )
    else:
        return (
            *max_loc,
            max_loc[0] + w,
            max_loc[1] + h,
            max_loc[0] + w // 2,
            max_loc[1] + h // 2,
            max_val,
        )

def clip_img(img, area):
    if len(img.shape)==3:
        return img[area[1]:area[3], area[0]:area[2], :]
    else:
        return img[area[1]:area[3], area[0]:area[2]]

def psnr(img1, img2):
    mse = np.mean((img1 / 255.0 - img2 / 255.0) ** 2)
    if mse < 1.0e-10:
        return 100
    PIXEL_MAX = 1
    return 20 * np.log10(PIXEL_MAX / np.sqrt(mse))

def wait_for_img(target, f_cap, thr=35, dt=0.5):
    while True:
        img = f_cap()
        sc=psnr(target, img)
        if psnr(target, img)>=thr:
            break
        time.sleep(dt)