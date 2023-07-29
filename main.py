import glob
import os
import re
import unicodedata

import flet as ft
from mutagen.id3 import ID3, USLT  # noqa
from dataclasses import dataclass
import urllib.parse


@dataclass
class Data:
    input_path: str
    mp3_files: ['str']
    lyrics_files: ['str']
    selected: ft.Text | None


def main(page: ft.Page):
    runtime_data = Data('', [], [], None)

    def notify(text):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(text),
        )
        page.snack_bar.open = True

    def show_text(path):
        audio = ID3(path)
        try:
            lyrics_textfield_view.value = audio.getall('USLT')[0].text
        except AttributeError:
            pass
        except IndexError:
            pass
        page.update()

    def select_handler(e):
        if runtime_data.selected:
            runtime_data.selected.bgcolor = None
            lyrics_textfield_view.value = ''
        else:
            save_lyrics_button.disabled = False
        runtime_data.selected = e.control
        e.control.bgcolor = ft.colors.INVERSE_PRIMARY
        show_text(e.control.data)
        audio = ID3(e.control.data)
        hyperlink_button.text = e.control.content.controls[1].content.value
        hyperlink_button.url = f'https://ya.ru/search/?text=' + urllib.parse.quote(
            f'Текст песни {audio.get("TPE1").text[0]} - {audio.get("TIT2").text[0]}', safe='')
        page.update()

    def read_name(p: str) -> str:
        audio = ID3(p)
        return f'{audio.get("TPE1").text[0]} - {audio.get("TIT2").text[0]}'

    def update_list_view(result: [{str, str}] = None):
        new_list = []
        hyperlink_button.text = None
        lyrics_textfield_view.value = None
        for i, f in enumerate(runtime_data.mp3_files):
            if result:
                text_availability, tooltip = result[i]
                if song_list_view.controls[i].content.controls[2].content.value != '❌':
                    text_availability = "⚠️"
            else:
                text_availability = '❌'
                tooltip = 'Отсутствует в треке'
                try:
                    if ID3(f).getall("USLT")[0].text:
                        text_availability = '🎵✅'
                        tooltip = 'Загружен из трека'
                except AttributeError:
                    pass
                except IndexError:
                    pass
            new_list.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(str(i + 1)),
                                width=30,
                                alignment=ft.alignment.center_right,
                            ),
                            ft.Container(
                                content=ft.Text(read_name(f)),
                                width=340,
                            ),
                            ft.Container(
                                content=ft.Text(text_availability, font_family='Apple Color Emoji'),
                                width=50,
                                alignment=ft.alignment.center,
                                tooltip=tooltip,
                            ),
                        ],
                    ),
                    data=f,
                    on_click=select_handler,
                    padding=10,
                    border_radius=3
                )
            )

        song_list_view.controls.clear()
        song_list_view.controls = new_list
        page.update()

    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.path:
            pb.visible = True
            page.update()
            runtime_data.input_path = e.path
            runtime_data.mp3_files = sorted(glob.glob(f'{runtime_data.input_path}/*.mp3'),
                                            key=lambda x: read_name(x))
            runtime_data.lyrics_files = sorted(glob.glob(f'{runtime_data.input_path}/*.txt'))
            update_list_view()
            add_texts_button.visible = True
            handle_space.visible = True
            pb.visible = False
            page.update()

    def add_lyrics(audio: ID3(), text: str, selected: ft.Container = None):
        audio.setall('USLT', [USLT(encoding=3, text=text.strip('\n').rstrip('\n'))])  # noqa
        if selected:
            selected.content.controls[2].content.value = '🫸✅'  # noqa
            selected.content.controls[2].tooltip = 'Добавлен вручную'  # noqa
            notify(f'Текст добавлен для трека {selected.content.controls[1].content.value}')  # noqa
            page.update()
        audio.save()

    def sort_list(_):
        if len(song_list_view.controls) > 0:
            sort, symbol = (True, '▼') if not song_list_view.data else (False, '▲')
            song_list_view.data = sort
            name_list_header.value = f'Название {symbol}'
            song_list_view.controls = sorted(song_list_view.controls,
                                             key=lambda x: x.content.controls[1].content.value,
                                             reverse=sort)
            page.update()

    def add_texts_from_dir(_):
        pb.visible = True
        page.update()
        result = []
        for i, mp3_path in enumerate(runtime_data.mp3_files):
            audio = ID3(mp3_path)
            for lyrics_path in runtime_data.lyrics_files:
                artist = re.sub(
                    r'[0-9]', '', unicodedata.normalize(
                        'NFKC', audio.get("TPE1").text[0].lower()).replace('ё', 'е').strip())
                title = re.sub(
                    r'[0-9]', '', unicodedata.normalize(
                        'NFKC', audio.get("TIT2").text[0].lower()).replace('ё', 'е').strip())
                lyrics_filename = unicodedata.normalize('NFKC', os.path.splitext(os.path.basename(lyrics_path))[
                    0].lower()).replace('ё', 'е')
                print(title in lyrics_filename, title, lyrics_filename)
                if artist in lyrics_filename and title in lyrics_filename:
                    with open(lyrics_path, "r", encoding="utf-8") as file:
                        text = file.read()
                        lines = text.split('\n')
                        if lines[0].startswith("Текст песни"):
                            del lines[0]
                        if lines[len(lines) - 1].startswith('track id:'):
                            del lines[len(lines) - 1]
                        text = '\n'.join(lines)
                        add_lyrics(audio, text)
                    result.append(('📁✅', 'Добавлен из папки'))
                    break
            try:
                result[i]
            except IndexError:
                result.append(('❗', 'Файл с текстом отсутствует'))
        update_list_view(result)
        pb.visible = False
        page.update()

    page.window_width = 900
    page.window_height = 800
    page.window_resizable = False
    page.update()

    input_dialog = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(input_dialog)

    song_list_view = ft.ListView(data=False)
    name_list_header = ft.Text(f'Название ▲')
    song_list_view_header = ft.Row(
        controls=[
            ft.Container(
                content=ft.Text('#'),
                width=30,
                alignment=ft.alignment.center_right,
            ),
            ft.Container(
                content=name_list_header,
                width=340,
                on_click=sort_list
            ),
            ft.Container(
                content=ft.Text('Текст'),
                width=50,
                alignment=ft.alignment.center
            ),
        ],
    )

    lyrics_textfield_view = ft.TextField(multiline=True, max_lines=None,
                                         expand=True, min_lines=40, text_size=10,
                                         text_style=ft.TextStyle(font_family='Courier'))

    save_lyrics_button = ft.ElevatedButton(
        text='Сохранить',
        width=float('inf'),
        on_click=lambda _: add_lyrics(
            ID3(runtime_data.selected.data),
            lyrics_textfield_view.value,
            runtime_data.selected
        ),
        disabled=True
    )

    add_texts_button = ft.ElevatedButton(
        text='Добавить тексты',
        on_click=add_texts_from_dir,
        visible=False
    )

    hyperlink_button = ft.TextButton()

    handle_space = ft.Row(
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=song_list_view_header,
                            padding=ft.padding.symmetric(horizontal=20, vertical=0),
                            width=500,
                        ),
                        ft.Container(
                            content=song_list_view,
                            width=500,
                            height=570,
                            border_radius=3,
                            padding=ft.padding.symmetric(horizontal=10, vertical=0),
                            border=ft.border.all(width=1, color=ft.colors.SHADOW)
                        ),
                    ],
                ),
                padding=10,
                border_radius=6,
                bgcolor=ft.colors.ON_SECONDARY,
            ),
            ft.Container(
                ft.Column(
                    controls=[
                        ft.Container(
                            content=hyperlink_button,
                            border_radius=3,
                            padding=10
                        ),
                        lyrics_textfield_view,
                        save_lyrics_button
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                width=346,
                height=662,
                padding=10,
                border_radius=6,
                bgcolor=ft.colors.ON_SECONDARY,

            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.START,
        visible=False
    )
    pb = ft.ProgressBar(width=float('inf'), visible=False)
    page.add(
        ft.Container(pb, padding=0, margin=0),
        ft.Container(

            content=ft.Row(
                controls=[
                    ft.ElevatedButton(
                        text='Выбрать файлы',
                        on_click=lambda _: input_dialog.get_directory_path(),
                    ),
                    add_texts_button
                ],
            ),
            border_radius=6,
            bgcolor=ft.colors.ON_SECONDARY,
            padding=10
        ),
        handle_space

    )


if __name__ == '__main__':
    ft.app(main)
