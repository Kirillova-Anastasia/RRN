from __future__ import print_function
import argparse
from math import log10
import os
import torch
import torch.nn as nn
from torch.autograd import Variable
from torch.utils.data import DataLoader
from data import get_eval_set 
import time
import torch.backends.cudnn as cudnn
import cv2
import math
import sys
import datetime
from utils import Logger
import numpy as np
import torchvision.utils as vutils
from arch import RRN
import time

parser = argparse.ArgumentParser(description='PyTorch RRN Example')
parser.add_argument('--scale', type=int, default=4, help="super resolution upscale factor")
parser.add_argument('--testbatchsize', type=int, default=1, help='testing batch size')
parser.add_argument('--threads', type=int, default=32, help='number of threads for data loader to use')
parser.add_argument('--seed', type=int, default=0, help='random seed to use. Default=123')
parser.add_argument('--gpus', default=1, type=int, help='number of gpu')
parser.add_argument('--cuda',default=True, type=bool)
parser.add_argument('--layer', type=int, default=10, help='network layer')
parser.add_argument('--test_dir',type=str,default='/home/panj/data/Vid4')
parser.add_argument('--scene_name',type=str,default='')
#parser.add_argument('--test_dir',type=str,default='/home/panj/data/udm10')
#parser.add_argument('--test_dir',type=str,default='/home/panj/data/SPMC_test')
parser.add_argument('--save_test_log', type=str,default='./log/test')
#parser.add_argument('--pretrain', type=str, default='./model/RRN-5L.pth')
parser.add_argument('--num_layers', type=int, default=5)
parser.add_argument('--image_out', type=str, default='./out/')
opt = parser.parse_args()
gpus_list = range(opt.gpus)
systime = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
print(opt)

def main():
    sys.stdout = Logger(os.path.join(opt.save_test_log,'test_'+systime+'.txt'))
    if not torch.cuda.is_available():
        raise Exception('No Gpu found, please run with gpu')
    else:
        use_gpu = torch.cuda.is_available()
    if use_gpu:
        cudnn.benchmark = False
        torch.cuda.manual_seed(opt.seed)
    pin_memory = True if use_gpu else False 
    n_c = 128
    n_b = opt.num_layers
    rrn = RRN(opt.scale, n_c, n_b) # initial filter generate network
    print(rrn)
    print("Model size: {:.5f}M".format(sum(p.numel() for p in rrn.parameters())*4/1048576))
    print('===> {}L model has been initialized'.format(n_b))
    rrn = torch.nn.DataParallel(rrn, device_ids=gpus_list)
    print('===> load pretrained model')
    if os.path.isfile('./model/RRN-{}L.pth'.format(n_b)):
        rrn.load_state_dict(torch.load('./model/RRN-{}L.pth'.format(n_b), map_location=lambda storage, loc: storage))
        print('===> pretrained model is load')
    else:
        raise Exception('pretrain model is not exists')
    if use_gpu:
        rrn = rrn.cuda(gpus_list[0])

    print('===> Loading test Datasets')
    
    #scene_list = os.listdir(opt.test_dir)
    scene_list = [opt.scene_name]
    
    for scene_name in scene_list:
        test_set = get_eval_set(opt.test_dir, opt.scale, scene_name)
        test_loader = DataLoader(dataset=test_set, num_workers=opt.threads, batch_size=opt.testbatchsize, shuffle=False, pin_memory=pin_memory, drop_last=False)
        print('===> DataLoading Finished')
        test(test_loader, rrn, opt.scale, scene_name, n_c)
    
def test(test_loader, rrn, scale, scene_name, n_c):
    train_mode = False
    rrn.eval()
    out = []
    for image_num, x_input in enumerate(test_loader):
        B, _, T, _ ,_ = x_input.shape
        T = T - 1 # not include the padding frame
        with torch.no_grad():
            x_input = Variable(x_input).cuda(gpus_list[0])
            t0 = time.time()
            init = True
            for i in range(T):
                if init:
                    init_temp = torch.zeros_like(x_input[:,0:1,0,:,:])
                    init_o = init_temp.repeat(1, scale*scale*3, 1, 1)
                    init_h = init_temp.repeat(1, n_c, 1, 1)
                    h, prediction = rrn(x_input[:,:,i:i+2,:,:], init_h, init_o, init)
                    out.append(prediction)
                    init = False
                else:
                    h, prediction = rrn(x_input[:,:,i:i+2,:,:], h, prediction, init)
                    out.append(prediction)
        torch.cuda.synchronize()
        t1 = time.time()
        print("===> Timer: %.4f sec." % (t1 - t0))
        prediction = torch.stack(out, dim=2)
        prediction = prediction.squeeze(0).permute(1,2,3,0) # [T,H,W,C]
        prediction = prediction.cpu().numpy()[:,:,:,::-1] # tensor -> numpy, rgb -> bgr 
        for i in range(T):
            save_img(prediction[i], scene_name, i)
    return

def save_img(prediction, scene_name, image_num):
    #save_dir = os.path.join(opt.image_out, systime)
    save_dir = opt.image_out
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_dir = os.path.join(save_dir, scene_name)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    image_dir = os.path.join(save_dir, 'frame_{:03}'.format(image_num+1) + '.png')
    cv2.imwrite(image_dir, prediction*255, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    
def bgr2ycbcr(img, only_y=True):
    '''same as matlab rgb2ycbcr
    only_y: only return Y channel
    Input:
        uint8, [0, 255]
        float, [0, 1]
    Output:
        type is same as input
        unit8, [0, 255]
        float, [0, 1]
    '''
    in_img_type = img.dtype
    img.astype(np.float32)
    if in_img_type != np.uint8:
        img *= 255.
    # convert
    if only_y:
        rlt = np.dot(img, [24.966, 128.553, 65.481]) / 255.0 + 16.0
    else:
        rlt = np.matmul(img, [[24.966, 112.0, -18.214], [128.553, -74.203, -93.786],
                              [65.481, -37.797, 112.0]]) / 255.0 + [16, 128, 128]
    if in_img_type == np.uint8:
        rlt = rlt.round()
    else:
        rlt /= 255.
    return rlt.astype(in_img_type)

def crop_border_Y(prediction, shave_border=0):
    prediction = prediction[shave_border:-shave_border, shave_border:-shave_border]
    return prediction

def crop_border_RGB(target, shave_border=0):
    target = target[:,shave_border:-shave_border, shave_border:-shave_border,:]
    return target

def calculate_psnr(prediction, target):
    # prediction and target have range [0, 255]
    img1 = prediction.astype(np.float64)
    img2 = target.astype(np.float64)
    mse = np.mean((img1 - img2)**2)
    if mse == 0:
        return float('inf')
    return 20 * math.log10(255.0 / math.sqrt(mse))

def ssim(prediction, target):
    C1 = (0.01 * 255)**2
    C2 = (0.03 * 255)**2
    img1 = prediction.astype(np.float64)
    img2 = target.astype(np.float64)
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())
    mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]  # valid
    mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
    mu1_sq = mu1**2
    mu2_sq = mu2**2
    mu1_mu2 = mu1 * mu2
    sigma1_sq = cv2.filter2D(img1**2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(img2**2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return ssim_map.mean()

def calculate_ssim(img1, img2):
    '''
    calculate SSIM
    the same outputs as MATLAB's
    img1, img2: [0, 255]
    '''
    if not img1.shape == img2.shape:
        raise ValueError('Input images must have the same dimensions.')
    if img1.ndim == 2:
        return ssim(img1, img2)
    elif img1.ndim == 3:
        if img1.shape[2] == 3:
            ssims = []
            for i in range(3):
                ssims.append(ssim(img1, img2))
            return np.array(ssims).mean()
        elif img1.shape[2] == 1:
            return ssim(np.squeeze(img1), np.squeeze(img2))
    else:
        raise ValueError('Wrong input image dimensions.')



if __name__=='__main__':
    with open(os.path.join(opt.image_out, 'RRN-{}L.txt'.format(opt.num_layers)), 'a') as f:
        f.write('OK ' + opt.scene_name + '\n')
    begin = time.time()

    main()

    end = time.time()
    with open(os.path.join(opt.image_out, 'RRN-{}L.txt'.format(opt.num_layers)), 'a') as f:
        f.write('Full time on {}: {}\n'.format(opt.scene_name, end - begin))