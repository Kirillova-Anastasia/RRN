# Running on your own dataset
1) We used `pytorch/pytorch:1.0.1-cuda10.0-cudnn7-devel` docker. Directory with input images is mounted as `/dataset`, results will be saved in `/output`, directory with code is mounted as `/RRN`. You should set  `--shm-size 8G` parameter.
2) Enter directory `/RRN`. See `RRN.sh` script for installation commands and running example.

![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)
![PyTorch 1.1](https://img.shields.io/badge/pytorch-1.1-yellow.svg)

# Recurrent Residual Network for Video Super-resolution (RRN)

The *official* implementation for the [Revisiting Temporal Modeling for Video
Super-resolution] which is accepted by [BMVC-2020].

![framework](figs/framework.PNG)

### Train
We utilize 4 GTX-1080TI GPUs for training.
```
python main.py
```

### Test
We utilize 1 GTX-1080TI GPU for testing.
Test the trained model with best performance by
```
python test.py
```
