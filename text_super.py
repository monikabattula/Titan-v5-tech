import cv2
from text_extractor import text_extractor
from translater_func import translater_func
from srt_generator import create_srt_file
from generate_final import generate_final

def text_super(video_path, baseName, translate_lang):
  cam = cv2.VideoCapture(video_path)
  fps = cam.get(cv2.CAP_PROP_FPS)
  print("FPS:", fps)
  subtitles = []
  time_interval = 4
  frame_interval = int(time_interval * fps)
  print(frame_interval)
  n = 0
  i = 0

  while True:
    ret, frame = cam.read()

    if n % frame_interval == 0:
      timestamp_ms = cam.get(cv2.CAP_PROP_POS_MSEC)
      timestamp_sec = timestamp_ms / 1000.0  # Convert milliseconds to seconds
      try:
        cv2.imwrite(f"static/outdir/{i}.jpg", frame)
      except:
        pass
      try:
        text = text_extractor(f"static/outdir/{i}.jpg")
      except:
        pass
      translated_text = translater_func(text, translate_lang.split("-").pop(0))
      subtitles.append((timestamp_sec, timestamp_sec + 4, translated_text))
      i += 1

    n += 1
    if ret is False:
      break

  create_srt_file(subtitles, "static/outdir/output.srt")
  generate_final(f"static/outdir/dubbedVideos/{baseName}[{translate_lang}].mp4", translate_lang)
  cam.release()
  cv2.destroyAllWindows()
