#!/usr/bin/env python

'''
markup.py
Интерфейс для разметки Пегтымельских петроглифов
НИУ Высшая школа экономики
Институт арехологии РАН
(С) Павел Лебедев, Василий Садовников, 2022

Инструкция:
1. указываем папку с оленями (images_dir), имя выходного файла (markup_filename) и список меток (marks)
2. запускаем markup.py на исполнение
3. метки, которые есть не у всех оленей можно пропускать (z, x)
4. листать оленей: пробел/-> - следующий, <- - предыдущий
5. подсказка по остальным клавишам - по нажатию Tab
6. поразмечали - пошли спать - запустили снова - все данные сохраняются и можно продолжить с любого места
7. изображения в папке можно дополнять и прореживать. при следующем запуске разметчика csv придет в соответствие
8. список меток можно дополнять, изменять. при следующем запуске разметчика csv придет в соответствие 
9. аккуратно. если исчезнет название какой-то метки, которая уже проставлена - она исчезнет у всех оленей

TODO:
Центрировать картинку в окне
Лучше обработать отображение подсказки (динамическое расположение, z-order)
Удаление метки
Перемещение существующей метки?
Переход на следующего оленя при постановке последней метки?
Переключение только между не проставленными метками?
'''

from typing import List, Dict, Tuple
import os
import csv
from os import listdir
from os.path import isfile, join
import tkinter as tk
from pathlib import Path
from PIL import ImageTk, Image


images_dir = Path('deers')
markup_filename = Path('deers_geom.csv')
labels = {
    'A': 'кончик носа',
    'B': 'задняя точка спины',
    'C': 'основание задних ног',
    'D': 'основание передних ног',
    'E': 'основание шеи',
    'F': 'середина спины',
    'H': 'середина брюшка',
    'I': 'передние копыта',
    'L': 'задние копыта',
    'K': 'кончик рогов',
    'N': 'затылок',
    'x': 'сустав передних ног',
    'y': 'сустав задних ног',
}


def load_markup():
    csv_data = {}
    empty_values = ('', None)
    if markup_filename.exists():
        with markup_filename.open('r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                coords = {}
                for key in labels:
                    x = row.get(key+'x')
                    y = row.get(key+'y')
                    if x not in empty_values and y not in empty_values:
                        coords[key] = (int(x), int(y))
                csv_data[row['filename']] = coords

    markup = []
    for path in sorted(images_dir.glob('*')):
        if path.name.endswith('.jpg') or path.name.endswith('.png'):
            markup.append({
                'filename': path.name,
                'labels': csv_data.get(path.name, {})
            })

    return markup


def save_markup(markup):
    fieldnames = ['filename']
    for key in labels:
        fieldnames.append(key+'x')
        fieldnames.append(key+'y')
    with markup_filename.open('w', newline='') as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=fieldnames, 
            restval='', 
            extrasaction='ignore'
        )
        writer.writeheader()
        for item in markup:
            row = {
                'filename': item['filename'],
            }
            for key, coord in item['labels'].items():
                row[key + 'x'] = coord[0]
                row[key + 'y'] = coord[1]
            writer.writerow(row)


class CanvasImage:
    def __init__(self, canvas, x=0, y=0, anchor='nw'):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.anchor = anchor

        self.canvas_image_id = None
        self.image_pil = None
        # ImageTk have refcounting bug, so we must keep reference to it
        self.image_tk = None
        self.scale = 1.0

    def load(self, filename):
        self.image_pil = Image.open(filename)
        self.image_tk = ImageTk.PhotoImage(self.image_pil)
        if self.canvas_image_id is None:
            self.canvas_image_id = self.canvas.create_image(
                self.x, self.y, image=self.image_tk, anchor=self.anchor
            )
        else:
            self.canvas.itemconfigure(self.canvas_image_id, image=self.image_tk)

    def rescale(self, scale):
        print('scale is', scale)
        self.scale = scale
        if not self.image_pil:
            return
        new_size = (
            int(round(scale * self.image_pil.width)), 
            int(round(scale * self.image_pil.height))
        )
        resized_img = self.image_pil.resize(new_size)
        self.image_tk = ImageTk.PhotoImage(resized_img)
        self.canvas.itemconfigure(self.canvas_image_id, image=self.image_tk)

    def fit(self, window_size):
        print('fit', window_size)
        if not self.image_pil:
            return
        scale = min(window_size[0] / self.image_pil.size[0], window_size[1] / self.image_pil.size[1])
        self.rescale(scale)

    @property
    def size(self):
        return self.image_pil.size if self.image_pil else None


class Cursor:
    def __init__(self, canvas):
        self.canvas = canvas
        self.created = False
        self.label_key = ''
        self.label_description = ''
        self.half = 50
        self.hidden = False

    def set_label(self, key, description):
        self.label_key = key
        self.label_description = description
        if self.created:
            self.canvas.itemconfigure('cursor_label', text=self.label_key)
            self.canvas.itemconfigure('cursor_description', text=self.label_description)

    def set_pos(self, x, y):
        if self.created:
            self.canvas.moveto('cursor', x, y)
            # the following code causes bugs
            # self.canvas.moveto('cursor_crosshair', x, y)
            # self.canvas.coords('cursor_label', x+25, y+1)
            # self.canvas.coords('cursor_description', x+25, y+4)
        else:
            self.created = True
            self.canvas.create_line(x, y, x+self.half, y, fill='red', tags=('cursor', 'cursor_crosshair'))
            self.canvas.create_line(x, y, x-self.half, y, fill='red', tags=('cursor', 'cursor_crosshair'))
            self.canvas.create_line(x, y, x, y+self.half, fill='red', tags=('cursor', 'cursor_crosshair'))
            self.canvas.create_line(x, y, x, y-self.half, fill='red', tags=('cursor', 'cursor_crosshair'))
            self.canvas.create_text(x+25, y-1, anchor='sw', fill='red', font="Arial 18", text=self.label_key, width=20, tags=('cursor', 'cursor_label'))
            self.canvas.create_text(x+25, y+3, anchor='nw', fill='red', font="Arial 13", text=self.label_description, width=70, tags=('cursor', 'cursor_description'))
            if self.hidden:
                self.hide()

    def show(self):
        self.hidden = False
        self.canvas.itemconfigure('cursor', state='normal')

    def hide(self):
        self.hidden = True
        self.canvas.itemconfigure('cursor', state='hidden')


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Petroglyphs Markup')
        self.geometry('800x600')

        self.canvas = tk.Canvas(self, bg='white')
        self.canvas.pack(expand=True, fill=tk.BOTH)
        # no robust method for getting canvas size :(
        # we should use this initialization and then track resize events
        self.canvas_size = (int(self.canvas['width']), int(self.canvas['height']))

        self.deer_image = CanvasImage(self.canvas, 0, 0, anchor='nw')

        self.markup = load_markup()
        self.current_index = 0
        self.current_label_index = 0
        self.screen_labels = {}
        self.labels_list = list(labels.items())

        self.cursor = Cursor(self.canvas)
        self.cursor.set_label(*self.labels_list[0])

        # self.set_mark('A', (100, 100))
        # self.set_mark('B', (200, 100))

        self.load_item()

        self.canvas.create_text(200, 300, text='',
                      justify=tk.RIGHT, anchor=tk.SE, font="Arial 13", fill='grey', tag='counter')
        self.update_counter()

                
        self.canvas.create_rectangle(0, 300, 500, 600,
            outline="black", fill="white", tag='help', state='hidden')

        help_text = self.canvas.create_text(30, 500, 
              text=
                "Tab\t\tToggle help\n" \
                "Left click\t\tPlace a mark or move existing\n" \
                "Right click\t\tRemove current mark\n" \
                "Space\t\tNext image\n" \
                "Right arrow\tNext image\n" \
                "Left arrow\t\tPrevious image\n" \
                "x\t\tNext mark\n" \
                "z\t\tPrevious mark\n" \
                "Escape\t\tSave and quit\n" \
                "Close window\tSave and quit",
              justify=tk.LEFT, anchor=tk.SW, font="Arial 15", fill='grey', tag='help', state='hidden')

        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.bind("<Escape>", lambda event: self.quit())
        self.bind("<space>", self.next_item)
        self.bind("<Right>", self.next_item)
        self.bind("<Left>", self.prev_item)
        self.bind("<Tab>", self.toggle_help)
        self.bind('<z>', lambda event: self.prev_mark())
        self.bind('<x>', lambda event: self.next_mark())
        self.canvas.bind('<Motion>', self.on_move)
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind('<Enter>', self.on_enter)
        self.canvas.bind('<Leave>', self.on_leave)
        

    @property
    def current_item(self):
        return self.markup[self.current_index]


    def on_move(self, event):
        self.cursor.set_pos(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))

    def next_item(self, event):
        self.current_index = (self.current_index + 1) % len(self.markup)
        self.update_counter()
        self.load_item()

    def prev_item(self, event):
        self.current_index = (self.current_index - 1) % len(self.markup)
        self.update_counter()
        self.load_item()

    def load_item(self):
        self.deer_image.load(images_dir / self.current_item['filename'])
        self.deer_image.fit(self.canvas_size)
        self.canvas.itemconfigure('mark', state='hidden')
        self.update_screen_marks()
        self.current_label_index = 0
        self.update_cursor()

    def toggle_help(self, event):
        if(self.canvas.itemcget('help', 'state') == 'normal'):
            self.canvas.itemconfigure('help', state='hidden')
        else:
            self.canvas.itemconfigure('help', state='normal')

    def update_cursor(self):
        self.cursor.set_label(*self.labels_list[self.current_label_index])

    def next_mark(self):
        self.current_label_index = (self.current_label_index + 1) % len(labels)
        self.update_cursor()

    def prev_mark(self):
        self.current_label_index = (self.current_label_index - 1) % len(labels)
        self.update_cursor()

    def update_screen_marks(self):
        self.canvas.delete('mark')
        for key, coord in self.current_item['labels'].items():
            x = coord[0] * self.deer_image.scale + 2    # +2 to compensate some internal offest
            y = coord[1] * self.deer_image.scale + 2    #
            self.canvas.create_oval(x-10, y-10, x+10, y+10, outline='red', tags='mark')
            self.canvas.create_text(x+16, y+16, fill='red', font='Arial 13', text=key, tags='mark')
            self.canvas.create_line(x-20, y, x+20, y, fill='red', tags='mark')
            self.canvas.create_line(x, y-20, x, y+20, fill='red', tags='mark')

    def set_mark(self, key, screen_coord):
        self.current_item['labels'][key] = (
            int(round(screen_coord[0] / self.deer_image.scale)),
            int(round(screen_coord[1] / self.deer_image.scale))
        )
        self.update_screen_marks()

    def set_screen_mark(self, key, coord):
        print(key, coord)
        x, y = coord
        tag = f'mark_{key}'
        if self.canvas.type(tag):
            self.canvas.itemconfigure(tag, state='normal')
            self.canvas.moveto(tag, *coord)
            self.canvas.coords(f'{tag}_text', *coord)
        else:
            self.canvas.create_oval(x-10, y-10, x+10, y+10, width=2, outline='red', tags=('mark', tag))
            self.canvas.create_text(x+20, y, fill='red', text=key, tags=('mark', tag))

    def on_canvas_resize(self, event):
        self.canvas_size = (event.width, event.height)
        self.deer_image.fit(self.canvas_size)
        self.update_screen_marks()
        self.canvas.moveto('counter', event.width-215, event.height-30)

    def on_click(self, event):
        key, description = self.labels_list[self.current_label_index]
        self.set_mark(key, (event.x, event.y))
        self.cursor.hide()

    def on_release(self, event):
        self.next_mark()
        self.cursor.show()  #first show, then setpos. otherwise - bugs.
        self.cursor.set_pos(event.x, event.y)

    def on_enter(self, event):
        self.canvas.config(cursor="none") 
        self.cursor.show()

    def on_leave(self, event):
        self.canvas.config(cursor="arrow") 
        self.cursor.hide()

    def update_counter(self):
        width, height = self.deer_image.size
        self.canvas.itemconfig('counter', text=f"{self.markup[self.current_index]['filename']}     {width}x{height}     {self.current_index+1} / {len(self.markup)}")


app = App()
app.mainloop()

save_markup(app.markup)
