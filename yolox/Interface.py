import argparse

from loguru import logger
import torch
import cv2

from yolox.data.data_augment import ValTransform
from yolox.data.datasets import COCO_CLASSES, GENSHIN_CLASSES
from yolox.utils import fuse_model, get_model_info, postprocess, vis

#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class Predictor(object):
    def __init__(
        self,
        model,
        exp,
        cls_names=COCO_CLASSES,
        trt_file=None,
        decoder=None,
        device="cpu",
        fp16=False,
        legacy=False,
    ):
        self.model = model
        self.cls_names = cls_names
        self.decoder = decoder
        self.num_classes = exp.num_classes
        self.confthre = exp.test_conf
        self.nmsthre = exp.nmsthre
        self.test_size = exp.test_size
        self.device = device
        self.fp16 = fp16
        self.preproc = ValTransform(legacy=legacy)
        if trt_file is not None:
            from torch2trt import TRTModule

            model_trt = TRTModule()
            model_trt.load_state_dict(torch.load(trt_file))

            x = torch.ones(1, 3, exp.test_size[0], exp.test_size[1]).cuda()
            self.model(x)
            self.model = model_trt

    def inference(self, img):
        img, _ = self.preproc(img, None, self.test_size)
        img = torch.from_numpy(img).unsqueeze(0)
        img = img.float()
        if self.device == "gpu":
            img = img.cuda()
            if self.fp16:
                img = img.half()  # to FP16

        with torch.no_grad():
            #t0 = time.time()
            outputs = self.model(img)
            if self.decoder is not None:
                outputs = self.decoder(outputs, dtype=outputs.type())
            outputs = postprocess(
                outputs, self.num_classes, self.confthre,
                self.nmsthre, class_agnostic=True
            )
            #logger.info("Infer time: {:.4f}s".format(time.time() - t0))
        return outputs

def make_cfg():
    cfg=argparse.Namespace()
    cfg.device="gpu"
    cfg.fp16=False
    cfg.conf=0.75
    cfg.nms=0.45
    cfg.tsize=640
    cfg.ckpt="yolox/ckpt/epoch_60_ckpt_s.pth"
    cfg.fuse=True
    cfg.legacy=False
    return cfg

class DetectorInterface:
    def __init__(self, exp, cfg=make_cfg()):
        logger.info("Args: {}".format(cfg))
        model = exp.get_model()
        logger.info("Model Summary: {}".format(get_model_info(model, exp.test_size)))

        if cfg.conf is not None:
            exp.test_conf = cfg.conf
        if cfg.nms is not None:
            exp.nmsthre = cfg.nms
        if cfg.tsize is not None:
            exp.test_size = (cfg.tsize, cfg.tsize)

        if cfg.device == "gpu":
            model.cuda()
            if cfg.fp16:
                model.half()  # to FP16
        model.eval()

        ckpt_file = cfg.ckpt
        logger.info("loading checkpoint")
        ckpt = torch.load(ckpt_file, map_location="cpu")
        # load the model state dict
        model.load_state_dict(ckpt["model"])
        logger.info("loaded checkpoint done.")

        if cfg.fuse:
            logger.info("\tFusing model...")
            model = fuse_model(model)

        self.predictor = Predictor(
            model, exp, GENSHIN_CLASSES, None, None,
            cfg.device, cfg.fp16, cfg.legacy,
        )

        self.exp = exp

    @torch.no_grad()
    def predict(self, img):
        ratio = min(self.predictor.test_size[0] / img.shape[0], self.predictor.test_size[1] / img.shape[1])
        outputs = self.predictor.inference(img)[0]
        if outputs is None:
            return None

        output = outputs.cpu()
        bboxes = output[:, 0:4]
        # preprocessing: resize
        bboxes /= ratio

        cls = output[:, 6]
        scores = output[:, 4] * output[:, 5]

        output=torch.cat((bboxes, cls.view(-1,1), scores.view(-1,1)), dim=1)[scores>self.exp.test_conf,:]

        return output #[l,t,r,b,cls,s]