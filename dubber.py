from pydub import AudioSegment
from google.cloud import texttospeech
# from google.cloud import translate_v2 as translate
from googletrans import Translator
# from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip, TextClip
from typing import NamedTuple, List, Optional, Sequence
from gender.test import predict_gender
import os
import shutil
import ffmpeg
import time
import sys
import tempfile
from dotenv import load_dotenv
import html
import pvleopard
load_dotenv()

leopard = pvleopard.create(access_key=os.environ["PV_ACCESS_KEY"], enable_automatic_punctuation=True, enable_diarization=True)

def extract_audio(videoPath, outputPath):
    video = VideoFileClip(videoPath)
    video.audio.write_audiofile(outputPath)

def speech_to_text(audioFilePath, srtFilePath):
    transcript, words = leopard.process_file(audioFilePath)
    print(transcript)
    print(words)

    sentences = extract_speaker_sentence(words, audioFilePath)
    print(sentences)
    return sentences

    # def second_to_timecode(x: float) -> str:
    #     hour, x = divmod(x, 3600)
    #     minute, x = divmod(x, 60)
    #     second, x = divmod(x, 1)
    #     millisecond = int(x * 1000.)
    #     return '%.2d:%.2d:%.2d,%.3d' % (hour, minute, second, millisecond)

    # def to_srt(
    #         words: Sequence[pvleopard.Leopard.Word],
    #         endpoint_sec: float = 1.,
    #         length_limit: Optional[int] = 16) -> str:

    #     def _helper(end: int) -> None:
    #         lines.append("%d" % section)
    #         lines.append(
    #             "%s --> %s" %
    #             (
    #                 second_to_timecode(words[start].start_sec),
    #                 second_to_timecode(words[end].end_sec)
    #             )
    #         )
    #         lines.append(' '.join(x.word for x in words[start:(end + 1)]))
    #         lines.append('')


    #     lines = list()
    #     section = 0
    #     start = 0
    #     for k in range(1, len(words)):
    #         if ((words[k].start_sec - words[k - 1].end_sec) >= endpoint_sec) or \
    #                 (length_limit is not None and (k - start) >= length_limit):
    #             _helper(k - 1)
    #             start = k
    #             section += 1
    #     _helper(len(words) - 1)

    #     return '\n'.join(lines)
    
    # with open(srtFilePath, 'w') as f:
    #     f.write(to_srt(words))

def extract_speaker_sentence(words, audioPath):
    sentences = []
    sentence = {}

    speakerGender = {}
    for i, word in enumerate(words):
        wordText = word.word
        if not sentence:
            sentence = {
                'text': [wordText],
                'speaker': word.speaker_tag,
                'start_time': word.start_sec,
                'end_time': word.end_sec,
            }
        elif word.speaker_tag != sentence['speaker']:
            if not sentence['speaker'] in speakerGender:
                path = generate_audio_path(sentence['start_time'], sentence['end_time'], audioPath)
                speakerGender[sentence['speaker']] = predict_gender(path)
                os.remove(path)

            sentence['text'] = ' '.join(sentence['text'])
            sentence['gender'] = speakerGender[sentence['speaker']]
            sentences.append(sentence)
            sentence = {
                'text': [wordText],
                'speaker': word.speaker_tag,
                'start_time': word.start_sec,
                'end_time': word.end_sec
            }
        else:
            sentence['text'].append(wordText)
            sentence['end_time'] = word.end_sec           

        if i+1 < len(words) and words[i+1].start_sec - word.end_sec > 1.0:
            if not sentence['speaker'] in speakerGender:
                path = generate_audio_path(sentence['start_time'], sentence['end_time'], audioPath)
                speakerGender[sentence['speaker']] = predict_gender(path)
                os.remove(path)

            sentence['text'] = ' '.join(sentence['text'])
            sentence['gender'] = speakerGender[sentence['speaker']]
            sentences.append(sentence)
            sentence = {}
        
    if sentence:
        if not sentence['speaker'] in speakerGender:
            path = generate_audio_path(sentence['start_time'], sentence['end_time'], audioPath)
            speakerGender[sentence['speaker']] = predict_gender(path)
            os.remove(path)
        sentence['text'] = ' '.join(sentence['text'])
        sentence['gender'] = speakerGender[sentence['speaker']]
        sentences.append(sentence)
        sentence = {}

    print(speakerGender)

    return sentences

def generate_audio_path(startTime, endTime, audioPath):
    segement = AudioSegment.from_mp3(audioPath)

    extract = segement[startTime * 1000 : endTime * 1000]
    destPath = f"static/outdir/speakerClips.wav"
    extract.export(destPath, format="wav")
    return destPath


def extract_sentences_from_srt(srtFilePath):
    sentences = []
    audio_splits = []
    durations = []

    def convert_to_sec(timeFormat):
      temp = timeFormat.split(',')
      micro_sec = int(temp[1]) * 0.001
      time = temp[0].split(':')
      seconds = int(time[0]) * 60 * 60 + int(time[1]) * 60 + int(time[2])
      return seconds + micro_sec

    with open(srtFilePath, 'r') as srt_file:
        lines = srt_file.readlines()

        current_sentence = ""

        for line in lines:
            line = line.strip()
            if '-->' in line:
              start_time = convert_to_sec(line[0:12])
              end_time = convert_to_sec(line[18:])

              audio_splits.append(start_time)
              durations.append(end_time - start_time)


            if not line:
                # Empty line indicates the end of a subtitle
                if current_sentence:
                    sentences.append(current_sentence)
                    current_sentence = ""
            elif not line.isdigit() and '-->' not in line:
                # Skip line numbers and timing lines
                current_sentence += "" + line

        # Add the last sentence if there is any
        if current_sentence:
            sentences.append(current_sentence)

    return sentences, audio_splits, durations

def translate_text(input, targetLang):
    target = targetLang.split("-")[0]
    translater = Translator()
    out = translater.translate(input, dest=target)
    print(out.text)
    return out.text


def speak(text, languageCode, speakerGender, speakingRate=1):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    if speakerGender == 'male':
        voiceName = f"{languageCode}-Standard-B"
    else:
        voiceName = f"{languageCode}-Standard-A"
    if not voiceName:
        voice = texttospeech.VoiceSelectionParams(
            language_code=languageCode, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
    else:
        voice = texttospeech.VoiceSelectionParams(
            language_code=languageCode, name=voiceName
        )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speakingRate
    )
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    return response.audio_content

def text_to_speech(text, languageCode, durationSecs, gender):
    temDirPath = f"static/outdir/temp"
    if(not os.path.exists(temDirPath)):
        os.mkdir(temDirPath)

    def find_duration(audio):
        # file = tempfile.NamedTemporaryFile(mode="w+b")
        # file.write(audio)
        # file.flush()
        # duration = AudioSegment.from_mp3(file.name).duration_seconds
        # file.close()
        with open(f"{temDirPath}/temp.mp3", 'wb') as f: 
                f.write(audio)
        duration = AudioSegment.from_mp3(f"{temDirPath}/temp.mp3").duration_seconds
        os.remove(f"{temDirPath}/temp.mp3")
        return duration

    baseAudio = speak(text, languageCode, gender)
    assert len(baseAudio)

    min_rate, max_rate = 0.25, 4
    currentDuration = find_duration(baseAudio)

    for i in range(2):
        currentDuration = find_duration(baseAudio)
        print(currentDuration, durationSecs)

        if abs(currentDuration - durationSecs) < 0.5:
            break

        ratio = currentDuration / durationSecs
        ratio = min(max(ratio, min_rate), max_rate)
        print(ratio)

        baseAudio = speak(text, languageCode, gender, speakingRate=ratio)
    
    return baseAudio, (durationSecs - currentDuration) if durationSecs > currentDuration else 0, currentDuration

def merge_audio(sentences, audioDir, videoPath, outputPath, lags, currentDurations):
    audioFiles = os.listdir(audioDir)
    audioFiles.sort(key=lambda x: int(x.split('.')[0]))
    tempDirPath = "static/outdir/temp"
    

    segments = [AudioSegment.from_mp3(os.path.join(audioDir, x)) for x in audioFiles]
    dubbed = AudioSegment.from_file(videoPath)

    emptySegment = AudioSegment.from_mp3("static/empty-audio.mp3")

    for sentence, segment, lag, duration in zip(sentences, segments, lags, currentDurations):
        dubbed = dubbed.overlay(segment, position=sentence['start_time'] * 1000, gain_during_overlay= -50)
        if lag != 0:
            emptyLag = emptySegment[:lag * 1000]
            dubbed = dubbed.overlay(emptyLag, position=sentence['start_time']+duration, gain_during_overlay = -50)
        

    # audioFile = tempfile.NamedTemporaryFile()
    tempFilePath = f"{tempDirPath}/temp.mp4"
    dubbed.export(tempFilePath, format="mp4")
    
    # dubbed.export(audioFile)
    # audioFile.flush()

    clip = VideoFileClip(videoPath)
    audio = AudioFileClip(tempFilePath)
    clip = clip.set_audio(audio)

    clip.write_videofile(outputPath, codec='libx264', audio_codec='aac')
    os.remove(tempFilePath)

def dub(videoPath, outputDir, srcLang, targetLangs=[], speakerCount=1, genAudio=False):

    videoName = os.path.split(videoPath)[-1].split('.')[0]
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)

    outputFiles = os.listdir(outputDir)

    if not f"{videoName}.mp3" in outputFiles:
        print("Extracting audio from video")
        outputAudioPath = f"{outputDir}/{videoName}.mp3"
        extract_audio(videoPath, outputAudioPath)

    sentences = []
    startPositions = []
    durations = []
    lags = []
    currentDurations = []

    if not "transcript.srt" in outputFiles:
        outputSrtPath = f"{outputDir}/transcript.srt"
        audioFilePath = f"{outputDir}/{videoName}.mp3"
        sentences = speech_to_text(audioFilePath, outputSrtPath)

        # sentences, startPositions, durations = extract_sentences_from_srt(outputSrtPath)
    
    translatedSentences = {}
    for lang in targetLangs:
        print(f"Translating the text")
        translatedSentences[lang] = []
        for sentence in sentences:
            print(sentence['text'])
            translatedSentences[lang].append(translate_text(sentence['text'], lang))
            print(translatedSentences)

    audioDir = f"{outputDir}/audioClips"
    if not "audioClips" in outputFiles:
        os.mkdir(audioDir)

    for lang in targetLangs:
        languageDir = f"{audioDir}/{lang}"
        if os.path.exists(languageDir):
            shutil.rmtree(languageDir)
        os.mkdir(languageDir)
        
        for i, text in enumerate(translatedSentences[lang]):
            audio, lag, currentDuration = text_to_speech(text, lang, sentences[i]['end_time'] - sentences[i]['start_time'], sentences[i]['gender'])

            lags.append(lag)
            currentDurations.append(currentDuration)

            with open(f"{languageDir}/{i}.mp3", 'wb') as f: 
                f.write(audio)

    dubbedDir = f"{outputDir}/dubbedVideos" 

    if not "dubbedVideos" in outputFiles:
        os.mkdir(dubbedDir)

    for lang in targetLangs:
        print(f"merging generated audio with video")
        outFile = f"{dubbedDir}/{videoName}[{lang}].mp4"
        merge_audio(sentences, f"{audioDir}/{lang}", videoPath, outFile, lags, currentDurations) 

    print("Done")