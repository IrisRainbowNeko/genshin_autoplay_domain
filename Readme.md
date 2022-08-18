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

下载训练权重放入```mmtracking/checkpoints/```文件夹中

[mmtracking训练权重](https://download.openmmlab.com/mmtracking/sot/siamese_rpn/siamese_rpn_r50_1x_lasot/siamese_rpn_r50_20e_lasot_20220420_181845-dd0f151e.pth)

## 安装yolox
安装方法参考[YOLOX](https://github.com/Megvii-BaseDetection/YOLOX)

下载原神数据集训练权重放入```yolox/ckpt/```文件夹中

[yolox训练权重](https://huggingface.co/7eu7d7/genshin_autoplay_domain/blob/main/epoch_60_ckpt_s.pth)

## 战斗策略配置
刷本战斗策略配置文件在```control/script/```文件夹内，目前有两个例子。
每个文件内可以配置多条战斗策略，每个策略设置一定冷却时间。
程序会按从上到下的优先级，运行最先冷却完的策略。

如果策略内添加了
```yaml
type: break
```
字段，则这一策略具有最高优先级，只要冷却好就优先执行，可以打断其他正在运行的策略。

支持的指令
```
switch 4 #切换到4号位角色
delay i #等待i秒
key e #敲击键盘按键e
key down e #按下键盘按键e不放
key up e #抬起键盘按键e
mouse l i #按下左键i秒
mouse r i #按下右键i秒
```

## 刷本配置
在```cfgs/```中配置刷本策略，其中有示例文件。

## 运行程序
以管理员模式启动命令行，运行程序:
```bash
python auto_play.py
```