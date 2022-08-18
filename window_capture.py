import win32api, win32con, win32gui, win32ui
import numpy as np
import cv2

class WindowCapture:
    def __init__(self, name, width=1920, height=1080):
        self.WINDOW_NAME = name
        self.DEFAULT_MONITOR_WIDTH = width
        self.DEFAULT_MONITOR_HEIGHT = height

        self.hwnd = win32gui.FindWindow(None, self.WINDOW_NAME)
        self.genshin_window_rect = win32gui.GetWindowRect(self.hwnd)

        self.ofx=0
        self.ofy=0

    def set_offset(self, ofx, ofy):
        self.ofx=ofx
        self.ofy=ofy

    def cap_box(self, box=None, resize=None):
        return self.cap(area=[box[0], box[1], box[2]-box[0], box[3]-box[1]], resize=resize)

    def cap(self, area=None, resize=None):
        if area is None:
            area=[0,0,self.DEFAULT_MONITOR_WIDTH, self.DEFAULT_MONITOR_HEIGHT]
        w, h = area[2:]

        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()

        dataBitMap.CreateCompatibleBitmap(dcObj, w, h)

        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (w, h), dcObj, (area[0]+self.ofx, area[1]+self.ofy), win32con.SRCCOPY)
        # dataBitMap.SaveBitmapFile(cDC, bmpfilenamename)
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray, dtype="uint8")
        img.shape = (h, w, 4)
        img=cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Free Resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        if resize is not None:
            img=cv2.resize(img, (int(resize[0]), int(resize[1])))

        return img