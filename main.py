import glob
import os
import re
from mutagen.id3 import ID3, USLT

folder_path = 'files'

mp3_files = glob.glob(f'{folder_path}/*.mp3')
txt_files = glob.glob(f'{folder_path}/*.txt')


def remove_track_id(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    updated_content = re.sub(r'track id: #[0-9]+', '', content)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)


def remove_first_line_if_match(text):
    lines = text.split('\n')
    if lines[0].startswith("Текст песни"):
        return '\n'.join(lines[1:])
    else:
        return text


if not mp3_files:
    print('⚠ В папке отсутствуют mp3 файлы!')
elif not txt_files:
    print('⚠ В папке отсутствуют txt файлы!')
elif not mp3_files and not mp3_files:
    print('⚠ Папка пустая!')
else:
    result = {}
    for mp3_path in mp3_files:
        mp3_file = os.path.splitext(os.path.basename(mp3_path))[0]
        audio = ID3(mp3_path)

        for txt_path in txt_files:
            remove_track_id(txt_path)
            txt_file = os.path.splitext(os.path.basename(txt_path))[0]
            txt_file_clean = re.sub(r'\s*\(.*\)', '', txt_file)
            if "USLT::rus" not in audio and txt_file_clean in mp3_file:
                with open(txt_path, "r", encoding="utf-8") as file:
                    target_txt = file.read()
                text = remove_first_line_if_match(target_txt)
                # desc = target_txt.splitlines()[0]
                audio["USLT::"] = USLT(encoding=3, lang=u'rus', desc=u'', text=text)
                audio.save()
                result[f'{mp3_file}'] = '✔ Текст успешно добавлен в mp3 файл'
                break
            elif "USLT::rus" in audio:
                result[f'{mp3_file}'] = '⚠ Текст на русском языке уже есть в mp3 файле'
            else:
                result[f'{mp3_file}'] = '⚠ Файл с текстом отсутствует'

    for key, value in result.items():
        print(f'{key}:\t{value}')
