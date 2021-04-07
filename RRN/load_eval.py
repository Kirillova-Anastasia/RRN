import os
import torch.utils.data as data
import torch
import numpy as np
from PIL import Image, ImageOps
import random

class DataloadFromFolderEval(data.Dataset): # load test dataset
    def __init__(self, image_dir, scale, scene_name, transform):
        super(DataloadFromFolderEval, self).__init__()
        alist = os.listdir(os.path.join(image_dir, scene_name))
        alist.sort()
        self.image_filenames = [os.path.join(image_dir, scene_name, x) for x in alist] 
        self.L = len(alist)
        self.scale = scale
        self.transform = transform # To_tensor
    def __getitem__(self, index):
        LR = []
        for i in range(self.L):
            temp = Image.open(self.image_filenames[i]).convert('RGB')
            LR.append(temp)
        LR = [np.asarray(img) for img in LR] 
        LR = np.asarray(LR)
        #if self.scale == 4: 
        #    target = np.lib.pad(target, pad_width=((0,0), (2*self.scale,2*self.scale), (2*self.scale,2*self.scale), (0,0)), mode='reflect')
        t, h, w, c = LR.shape
        LR = LR.transpose(1,2,3,0).reshape(h,w,-1) # numpy, [H',W',CT']
        if self.transform:
            LR = self.transform(LR) # Tensor, [CT',H',W']
        LR = LR.view(c,t,h,w)
        return LR
        
    def __len__(self):
        return 1 

