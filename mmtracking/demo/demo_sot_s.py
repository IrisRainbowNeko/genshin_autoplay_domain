# Copyright (c) OpenMMLab. All rights reserved.
import os
import os.path as osp
import tempfile
from argparse import ArgumentParser

import cv2
import mmcv
import numpy as np

from mmtrack.apis import inference_sot, init_model


def main():
    parser = ArgumentParser()
    parser.add_argument('config', help='Config file')
    parser.add_argument('--input', help='input video file')
    parser.add_argument('--output', help='output video file (mp4 format)')
    parser.add_argument('--script', default='../log_vv.txt')
    parser.add_argument('--checkpoint', help='Checkpoint file')
    parser.add_argument(
        '--device', default='cuda:0', help='Device used for inference')
    parser.add_argument(
        '--show',
        action='store_true',
        default=False,
        help='whether to show visualizations.')
    parser.add_argument(
        '--color', default=(0, 255, 0), help='Color of tracked bbox lines.')
    parser.add_argument(
        '--thickness', default=3, type=int, help='Thickness of bbox lines.')
    parser.add_argument('--fps', help='FPS of the output video')
    parser.add_argument('--gt_bbox_file', help='The path of gt_bbox file')
    args = parser.parse_args()

    with open(args.script, encoding='utf8') as f:
        lines = f.readlines()
        script=[]
        for x in lines:
            items = [y.strip() for y in x.split(';')]
            script.append([int(items[0]), np.array(eval(items[1]))*1.5])

    # load images
    if osp.isdir(args.input):
        imgs = sorted(
            filter(lambda x: x.endswith(('.jpg', '.png', '.jpeg')),
                   os.listdir(args.input)),
            key=lambda x: int(x.split('.')[0]))
        IN_VIDEO = False
    else:
        imgs = mmcv.VideoReader(args.input)
        IN_VIDEO = True

    OUT_VIDEO = False
    # define output
    if args.output is not None:
        if args.output.endswith('.mp4'):
            OUT_VIDEO = True
            out_dir = tempfile.TemporaryDirectory()
            out_path = out_dir.name
            _out = args.output.rsplit(os.sep, 1)
            if len(_out) > 1:
                os.makedirs(_out[0], exist_ok=True)
        else:
            out_path = args.output
            os.makedirs(out_path, exist_ok=True)
    fps = args.fps
    if args.show or OUT_VIDEO:
        if fps is None and IN_VIDEO:
            fps = imgs.fps
        if not fps:
            raise ValueError('Please set the FPS for the output video.')
        fps = int(fps)

    vid_writer = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (imgs._width, imgs._height))

    # build the model from a config file and a checkpoint file
    model = init_model(args.config, args.checkpoint, device=args.device)

    prog_bar = mmcv.ProgressBar(len(imgs))
    # test and show/save the images
    fid=0
    s_ptr=0
    init_bbox=np.array([100,100,200,200])
    for i, img in enumerate(imgs):
        if isinstance(img, str):
            img = osp.join(args.input, img)
            img = mmcv.imread(img)
        if s_ptr<len(script) and (i/fps)*1000 >= script[s_ptr][0]:
            #init_bbox = list(cv2.selectROI(args.input, img, False, False))

            # convert (x1, y1, w, h) to (x1, y1, x2, y2)
            init_bbox = script[s_ptr][1][:4]
            s_ptr+=1
            fid=0

        if i%2==0:
            result = inference_sot(model, img, init_bbox, frame_id=fid)
            fid+=1
        res = model.show_result(
            img,
            result,
            show=args.show,
            wait_time=0,
            out_file=None,
            thickness=args.thickness)
        vid_writer.write(res)
        prog_bar.update()

    '''if args.output and OUT_VIDEO:
        print(
            f'\nmaking the output video at {args.output} with a FPS of {fps}')
        mmcv.frames2video(out_path, args.output, fps=fps, fourcc='mp4v')
        out_dir.cleanup()'''
    vid_writer.release()


if __name__ == '__main__':
    main()
