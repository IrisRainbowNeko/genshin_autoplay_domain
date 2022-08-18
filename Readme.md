# 介绍
本项目融合了目标检测，目标跟踪模型，以及一些传统cv算法。
全自动刷原神秘境，全程无需人工操作。

目标检测部分通过构建怪物目标检测数据集，用半监督方法学习(标注5%)，为整个数据集标注伪标签。

## 注意
原神需要以 **1920x1080** 的分辨率运行，不支持其他分辨率。可以窗口化运行。

# 安装
首先安装基本依赖
```bash
pip install -r requirements.txt
```

安装mmcv-full
```bash
pip install openmim
mim install mmcv-full
```

安装vs2019或以上。

## 安装mmtracking
安装方法参考[mmtracking](https://github.com/open-mmlab/mmtracking)

## 安装yolox
安装方法参考[YOLOX](https://github.com/Megvii-BaseDetection/YOLOX)

## 运行程序
```bash
python auto_play.py
```