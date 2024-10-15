import subprocess

def generate_final(source_path, trans):
  subprocess.call(['ffmpeg', '-i', source_path, '-vf', 'subtitles=static/outdir/output.srt', f'static/outdir/{trans}.mp4'])