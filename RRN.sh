cd RRN
pip install --upgrade pip
pip install Pillow opencv-python
apt-get update && apt-get install -y python3-opencv
apt install -y libgl1-mesa-glx
apt-get install -y libglib2.0-0 libsm6 libxrender1  libxext6
pip install scipy torchvision

python3 eval.py --test_dir /dataset --scene_name test1_gauss_noise2 --image_out /output/RRN-5L --num_layers 5
python3 eval.py --test_dir /dataset --scene_name test2_bicubic_noise2 --image_out /output/RRN-5L --num_layers 5
python3 eval.py --test_dir /dataset --scene_name test2_gauss_noise2 --image_out /output/RRN-5L --num_layers 5

python3 eval.py --test_dir /dataset --scene_name test3_bicubic_noise2 --image_out /output/RRN-5L --num_layers 5
python3 eval.py --test_dir /dataset --scene_name test3_gauss_noise2 --image_out /output/RRN-5L --num_layers 5

python3 eval.py --test_dir /dataset --scene_name test1_gauss_noise2 --image_out /output/RRN-10L --num_layers 10
python3 eval.py --test_dir /dataset --scene_name test2_bicubic_noise2 --image_out /output/RRN-10L --num_layers 10
python3 eval.py --test_dir /dataset --scene_name test2_gauss_noise2 --image_out /output/RRN-10L --num_layers 10

python3 eval.py --test_dir /dataset --scene_name test3_bicubic_noise2 --image_out /output/RRN-10L --num_layers 10
python3 eval.py --test_dir /dataset --scene_name test3_gauss_noise2 --image_out /output/RRN-10L --num_layers 10