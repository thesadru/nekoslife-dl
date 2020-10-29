"""
Lets you scroll through images and then move them into directories.
I needed this so I can filter out the hentai I don't like.
Use it if you want.

You must enter keys and directories.
With the first argument being the key and every other argument in pairs,
where the firt arg is the key symbol and the second a save directory.
"""
import sys,os
import tkinter as tk
from pprint import pprint
from nekoslife_dl import NekosLifeScroller
from tkscroller import ImageDisplay,CategoryChooser

def update_display(imagedata):
    image_display.update_resolution(root.winfo_width(),root.winfo_height())
    image_display.update_display(*imagedata)
    
def new_session():
    nekoslife.new_session(category_chooser.get_category())
    update_display(nekoslife.get_current_image())

def reset_session():
    nekoslife.reset_session(category_chooser.get_category())
    update_display(nekoslife.get_current_image())


def key_pressed(event):
    keysym = event.keysym
    print(f'Pressed "{keysym}"',end='')
    
    if keysym == trash_keysym:
        print(', deleting file.')
        remove = True
    elif keysym not in paths:
        print(', no behaviour set.')
        return
    else:
        old_path = os.path.realpath(nekoslife.current_image)
        filename = os.path.split(nekoslife.current_image)[1]
        path = os.path.realpath(os.path.join(paths[keysym],filename))
        os.renames(old_path,path)
        print(f', moving to {path}.')
        remove = False

    update_display(nekoslife.get_next_image(remove=remove))

def update_loaded():
    category_chooser.loaded.configure(text=f'\tloaded images: {len(nekoslife.listdir())}')
    root.after(500,update_loaded)

if __name__ == '__main__':
    print('INITIALIZING')
    
    if len(sys.argv) < 2:
        raise ValueError('You must enter a trash keysym. Reffer to documentation.')
    
    trash_keysym = sys.argv[1]
    paths = {sys.argv[i]:sys.argv[i+1] for i in range(2,len(sys.argv)-1,2)}
    pprint(paths)
    
    nekoslife = NekosLifeScroller(download_threads=3)

    W,H = 400,400
    root = tk.Tk('nekos.life sorter')
    root.geometry(f'{W}x{H}')
    
    category_chooser = CategoryChooser(root,
        nekoslife.ENDPOINT_TYPES,nekoslife.ENDPOINT_FORMATS,nekoslife.get_endpoints())
    category_chooser.grid(row=0)

    image_display = ImageDisplay(root)
    image_display.update_resolution(W,H)
    image_display.grid(row=1)

    print('GETTING IMAGES')
    reset_session()
    update_loaded()

    root.bind('<Key>',key_pressed)
    root.mainloop()