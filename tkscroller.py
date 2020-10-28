import math
import time
import tkinter as tk
from pprint import pprint
from tkinter import ttk

from PIL import Image, ImageTk

from scroller import NekosLifeScroller


class ImageDisplay(tk.Frame):
    MAXWIDTH, MAXHEIGHT = 1000, 600
    IMGNORMALIZE = False
    fontsize = 12

    def __init__(self, master):
        super().__init__(master)

        self.label = tk.Label(self, font=("Arial", self.fontsize), compound='top')
        self.label.pack()

    def resize_img(self, img):
        if self.MAXWIDTH > 0 and self.MAXHEIGHT > 0:
            ratio = min(self.MAXWIDTH/img.width, self.MAXHEIGHT/img.height)
        elif self.MAXWIDTH > 0:
            ratio = self.MAXWIDTH/img.width
        elif self.MAXHEIGHT > 0:
            ratio = self.MAXHEIGHT/img.height
        else:
            ratio = 1

        if self.IMGNORMALIZE:
            # normalizes ratio to make it multiplied/divided by a whole number (x*N | x/N)
            if ratio >= 1:
                ratio = math.floor(ratio)
            else:
                ratio = 1/math.ceil(1/ratio)

        width = int(img.width*ratio)
        height = int(img.height*ratio)
        if width == 0 or height == 0:
            width = height = 1

        return img.resize((width, height))

    def update_display(self, imgpath, filename):
        img = Image.open(imgpath)
        img = self.resize_img(img)
        img = ImageTk.PhotoImage(img)
        
        self.update_resolution(root.winfo_width(),root.winfo_height())

        self.label.configure(text=filename, image=img)
        self.label.image = img

    def update_resolution(self, maxwidth, maxheight):
        self.MAXWIDTH = maxwidth
        self.MAXHEIGHT = maxheight-12-self.fontsize-category_chooser.winfo_height()

class CategoryChooser(tk.Frame):
    RESET_ON_CHANGE = True
    def __init__(self, master):
        super().__init__(master)
            
        self.imgtype     = tk.StringVar()
        self.imgformat   = tk.StringVar()
        self.imgcategory = tk.StringVar()
        
        
        self.omtype      = ttk.OptionMenu(self,self.imgtype,'sfw',
                                          *nekoslife.ENDPOINT_TYPES,command=self.update_category)
        self.omformat    = ttk.OptionMenu(self,self.imgformat,'img',
                                          *nekoslife.ENDPOINT_FORMATS,command=self.update_category)
        self.omcategory  = ttk.OptionMenu(self,self.imgcategory,'cat',
                                          *self.get_category_endpoints(),command=self.reset_session)
        
        self.last_category = self.get_category()
        
        self.loaded = tk.Label(self)
        
        self.omtype    .grid(column=0,row=0)
        self.omformat  .grid(column=1,row=0)
        self.omcategory.grid(column=2,row=0)
        self.loaded.grid(column=3,row=0,sticky='e')
    
    def get_category_endpoints(self):
        endpoints = nekoslife.get_endpoints()
        return endpoints[self.imgtype.get()][self.imgformat.get()]
    
    def get_category(self):
        return self.imgtype.get(),self.imgformat.get(),self.imgcategory.get()

    def update_category(self,event=''):
        print('UPDATE CATEGORY to',event)
        self.omcategory.set_menu(*self.get_category_endpoints())
        self.reset_session()
    
    def reset_session(self,event=''):
        if not self.RESET_ON_CHANGE and not event:
            return
        
        print('RESETING SESSION to',event)
        reset_session()

def new_session():
    nekoslife.new_session(category_chooser.get_category())
    image_display.update_display(*nekoslife.get_current_image())

def reset_session():
    nekoslife.reset_session(category_chooser.get_category())
    image_display.update_display(*nekoslife.get_current_image())

def key_pressed(event):
    if event.keysym == "Right":
        nekoslife.get_images_ready(*category_chooser.get_category())
        image_display.update_display(*nekoslife.get_next_image())

def update_loaded():
    category_chooser.loaded.configure(text=f'\tloaded images: {len(nekoslife.listdir())}')
    root.after(500,update_loaded)

if __name__ == '__main__':
    nekoslife = NekosLifeScroller()

    W,H = 400,400
    root = tk.Tk('nekos.life viewer')
    root.geometry(f'{W}x{H}')

    category_chooser = CategoryChooser(root)
    category_chooser.grid(row=0)

    image_display = ImageDisplay(root)
    image_display.update_resolution(W,H)
    image_display.grid(row=1)

    reset_session()
    update_loaded()

    root.bind('<Key>',key_pressed)
    root.mainloop()