from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from pprint import pprint
from scroller import NekosLifeScroller
import math

class ImageDisplay(Frame):
    MAXWIDTH,MAXHEIGHT = 1000,600
    IMGNORMALIZE = False
    fontsize = 12
    def __init__(self, master):
        super().__init__(master)
        
        self.label = Label(self, font=("Arial", self.fontsize), compound='top')
        self.label.pack()
    
    def resize_img(self,img):
        if self.MAXWIDTH > 0 and self.MAXHEIGHT > 0:
            ratio = min(self.MAXWIDTH/img.width,self.MAXHEIGHT/img.height)
        elif self.MAXWIDTH > 0:
            ratio = self.MAXWIDTH/img.width
        elif self.MAXHEIGHT > 0:
            ratio = self.MAXHEIGHT/img.height
        else:
            ratio = 1
            
        
        if self.IMGNORMALIZE:
            # normalizes ratio to make it multiplied by a whole number (xN)
            if ratio >= 1:
                ratio = math.floor(ratio)
            else:
                ratio = 1/math.ceil(1/ratio)
        
        width = int(img.width*ratio)
        height = int(img.height*ratio)
        
        return img.resize((width,height))
        

    def update_display(self,imgpath,filename):
        img = Image.open(imgpath)
        img = self.resize_img(img)
        img = ImageTk.PhotoImage(img)
        
        self.label.configure(text=filename,image=img) 
        self.label.image = img

    def update_resolution(self,maxwidth,maxheight):
        self.MAXWIDTH = maxwidth
        self.MAXHEIGHT = maxheight-12-self.fontsize-ctg_chooser.winfo_height()

class CategoryChooser(Frame):
    
    def __init__(self, master):
        super().__init__(master)
            
        self.imgtype     = StringVar()
        self.imgformat   = StringVar()
        self.imgcategory = StringVar()
        
        
        self.omtype      = ttk.OptionMenu(self,self.imgtype,'sfw',*nl.ENDPOINT_TYPES)
        self.omformat    = ttk.OptionMenu(self,self.imgformat,'img',*nl.ENDPOINT_FORMATS)
        self.omcategory  = ttk.OptionMenu(self,self.imgcategory,'cat')
        
        self.imgtype    .trace('w',self.update_category)
        self.imgformat  .trace('w',self.update_category)
        self.imgcategory.trace('w',self.reset_session)
        
        self.omtype    .grid(column=0,row=0)
        self.omformat  .grid(column=1,row=0)
        self.omcategory.grid(column=2,row=0)
    
    
    def update_category(self,*event,reset=True):
        endpoints = nl.get_endpoints()
        choices = endpoints[self.imgtype.get()][self.imgformat.get()]
        self.omcategory.set_menu(*choices)
        if reset:
            self.reset_session()
    
    def reset_session(self,*event):
        nl.reset_session(self.get_category())
        image_display.update_display()
    
    def get_category(self):
        return self.imgtype.get(),self.imgformat.get(),self.imgcategory.get()
    
    
def update_display(resolution=True):
    if resolution:
        image_display.update_resolution(root.winfo_width(),root.winfo_height())
    image_display.update_display(*nl.get_next_image())
    image_display.grid(row=1)


def key_pressed(event: Event):
    if event.keysym == "Right":
        nl.delete_current_image()
        print(f"deleted {nl.current_image}")
        nl.get_images_ready(*ctg_chooser.get_category())
        update_display()
        
    elif event.keysym == "Left":
        nl.restore_previous()
        print(f"restoring {nl.current_image}")
        update_display()
        

nl = NekosLifeScroller()
nl.get_images_ready('sfw','img','cat')

W,H = 400,400
root = Tk('nekos.life viewer')
root.geometry(f'{W}x{H}')

ctg_chooser = CategoryChooser(root)
image_display = ImageDisplay(root)

ctg_chooser.update_category(reset=False)
ctg_chooser.grid(row=0)

image_display.update_resolution(W,H)
update_display(resolution=False)




root.bind('<Key>',key_pressed)

root.mainloop()
