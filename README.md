## First run a dummy to download the weights

## 4 threads is a good utilization of GPU

## Run the test in `video_urls` for different platforms

## Configure `.env`

See `~/.config/rclone/rclone.conf`

## Configure `video_urls.txt`

## Dependencies(on Ubuntu)

```sh
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv 
python3 -m venv ~/myenv
source ~/myenv/bin/activate
pip install yt-dlp boto3 uuid python-dotenv openai-whisper
```

## Clone and Run

```sh
source ~/myenv/bin/activate
cd ~
git clone https://github.com/jimchen2/whisper-video-s3


cd ~/whisper-video-s3 
python run.py -t 1
```

## Installing ffmpeg

```sh
# on vastai
# conda install -c conda-forge ffmpeg=6 cudatoolkit

# Verify
ffmpeg -hwaccels
```