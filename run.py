import os
import subprocess
import uuid
from dotenv import load_dotenv
from s3_operations import upload_to_s3
from transcription import transcribe_video
from translation import translate_vtt
from utils import read_urls_from_file, get_filename_and_extension, cleanup_files

# Load environment variables from .env file
load_dotenv()

def download_video(url, extension):
    temp_filename = f"temp_{uuid.uuid4().hex}"+extension
    subprocess.run([
        'yt-dlp',
        '-o', temp_filename,
        '-f', 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        '-N', '10',
        url
    ])
    return temp_filename

def transcode_to_mp4(input_file):
    output_file = f"{os.path.splitext(input_file)[0]}.mp4"
    probe = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', 
                                     '-count_packets', '-show_entries', 'stream=width,height', 
                                     '-of', 'csv=p=0', input_file]).decode('utf-8').strip().split(',')
    width, height = map(int, probe)

    # Calculate target dimensions
    target_height = height
    target_width = height * 16 // 9
    
    if target_width < width:
        target_width = width
        target_height = width * 9 // 16

    # Construct FFmpeg command
    command = [
        'ffmpeg',
        '-hwaccel', 'cuda',  # Use CUDA hardware acceleration
        '-i', input_file,
        '-vf', f'pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2',
        '-c:v', 'h264_nvenc',  # Use NVIDIA NVENC encoder
        '-preset', 'p4',  # Fastest preset for NVENC
        '-tune', 'hq',  # High quality tuning
        '-b:v', '5M',  # Set a target bitrate (adjust as needed)
        '-maxrate', '10M',  # Maximum bitrate
        '-bufsize', '15M',  # VBV buffer size
        '-c:a', 'copy',  # Copy audio without re-encoding
        output_file
    ]
    
    subprocess.run(command)
    os.remove(input_file)
    return output_file

def process_video(url):
    try:
        # Get the original filename that yt-dlp would use
        original_filename, extension = get_filename_and_extension(url)

        # Step 1: Download video
        downloaded_video = download_video(url,extension)
        
        # Step 2: Transcode to MP4
        mp4_video = transcode_to_mp4(downloaded_video)
        
        # Step 3: Transcribe to Russian
        russian_subs = transcribe_video(mp4_video)
        
        # Step 4: Translate Russian VTT to English and combine
        translated_subs = translate_vtt(russian_subs)
        
        # Step 5: Upload to S3
        upload_to_s3(translated_subs, os.getenv('S3_BUCKET'), original_filename)
        
        # Clean up
        cleanup_files(mp4_video, russian_subs, translated_subs)
        
        print(f"Successfully processed and uploaded: {url}")
    except Exception as e:
        print(f"Error processing {url}: {e}")

def main():
    urls_file = 'video_urls.txt'  # Name of the file containing video URLs
    video_urls = read_urls_from_file(urls_file)
    
    for url in video_urls:
        process_video(url)

if __name__ == "__main__":
    main()