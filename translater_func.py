# from googletrans import Translator
# translater = Translator()

# def translater_func(text, dest_lang):
#   out = translater.translate(text, dest=dest_lang)
#   print(out.text)
#   return out.text

from google.cloud import translate_v2 as translate

def translater_func(input, targetLang):
  translate_client = translate.Client()
  result = translate_client.translate(input, target_language=targetLang, source_language="en")
  print(result['translatedText'])
  return result['translatedText']