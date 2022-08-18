import os
import os.path as osp
import tempfile
from argparse import ArgumentParser

import cv2
import mmcv
import torch

from mmtrack.apis import inference_sot, init_model

class TrackerInterface:
    def __init__(self, config='mmtracking/configs/sot/siamese_rpn/siamese_rpn_r50_20e_lasot.py',
                       checkpoint='mmtracking/checkpoints/siamese_rpn_r50_20e_lasot_20220420_181845-dd0f151e.pth'):
        self.config=config
        self.checkpoint=checkpoint
        self.device='cuda:0'

        self.model = init_model(config, checkpoint, device=self.device)

    def reset(self, init_bbox):
        self.frame_id=0
        self.init_bbox=init_bbox

    @torch.no_grad()
    def predict(self, img):
        result = inference_sot(self.model, img, self.init_bbox, frame_id=self.frame_id)
        self.frame_id+=1
        return result['track_bboxes']