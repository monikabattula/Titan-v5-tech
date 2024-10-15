from flask import Flask, render_template, url_for, request, send_file, Response
from fileinput import filename
from io import BytesIO
import io, shutil, os, glob
from dubber import dub
from text_super import text_super
import argparse
from pytube import YouTube
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
VIDEO_SAVE_DIRECTORY = "./video"

app = Flask(__name__)

baseName = None
f = None
translate_lang = None

@app.route('/', methods = ['POST', 'GET'])
def index():
  langs = {
    "hi-IN": "Hindi",
    "pa-IN": "Punjabi",
    "te-IN": "Telugu",
    "ta-IN": "Tamil",
    "mr-IN": "Marathi",
    "bn-IN": "Bengali"
  }
  if request.method == "POST":
    global video_data
  if request.method == "POST":
    url = request.form.get('url')
    global baseName, f, translate_lang
    translate_lang = request.form.getlist('lang')
    translate = request.form.get('super')
    print(translate_lang)
    print(url)
    if url != "" and download(url) == "video was downloaded successfully":
      # print("mew")
      file = os.listdir('video/')[0]
      # print(file)
      filename = file
      f = open(f"video/{file}")
    else:
      # print("phew")
      f = request.files['file']
      filename = f.filename
      f.save('video/' + filename)

    print(translate)
    dub('video/' + filename, 'static/outdir', 'en-IN', translate_lang, speakerCount=1)
    baseName = filename.split('.')[0]
    print("baseName:", baseName)
    if translate:
      for lang in translate_lang:
        text_super('video/' + filename, baseName, lang)
    print(filename)
    return render_template('video-preview.html',baseName=baseName, translate_lang = translate_lang, translate = translate)
  else:
    try:
      shutil.rmtree('static/outdir')
    except:
      pass

    try:
      files = glob.glob('video/*')
      for f in files:
        os.remove(f)
    except:
      pass
    
    return render_template('index.html')


# @app.route('/download', methods = ['POST', 'GET'])
# def download():
#   global baseName, f, translate_lang
#   return send_file(f"static/outdir/dubbedVideos/{baseName}[{translate_lang}].mp4", as_attachment=True, download_name=f"{baseName}[{translate_lang}].mp4")

def download(video_url):
  video = YouTube(video_url)
  video = video.streams.get_highest_resolution()

  try:
    video.download(VIDEO_SAVE_DIRECTORY)
  except:
    print("Failed to download video")
    return ("Failed to download video")

  print("video was downloaded successfully")
  return("video was downloaded successfully")

if __name__ == '__main__':
  app.run(debug = True, port=3000)