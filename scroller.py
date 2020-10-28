from nekoslife import NekosLife
import os,time,random

class NekosLifeScroller(NekosLife):
    MAX_IMAGES = 60
    current_image = None
    
    def __init__(self,*args,**kwargs):
        super().__init__('.temp',*args,**kwargs)

        files = self.listdir()
        if len(files) > 0:
            self.current_image = files[0]
    
    def listdir(self):
        """
        Lists all files in savefolder.
        """
        files = []
        for i in os.listdir(self.save_folder):
            if os.path.splitext(i)[-1] == '.000':
                continue
            path = os.path.join(self.save_folder,i)
            if os.path.isfile(path):
                files.append(path)
        
        return files


    def get_images_ready(self,imgtype: str, imgformat: str, imgcategory: str):
        """
        Downloads to fill `MAX_IMAGES`.
        For optimization downloads only when planned download would be more than `MAX_IMAGE_COUNT`
        """
        total_downloaded = len(self.listdir())+self.dlqueue.qsize()
        amount = self.MAX_IMAGES-total_downloaded
        
        if amount < self.MAX_IMAGE_COUNT:
            return []
        return self.get_multiple_images(imgtype,imgformat,imgcategory,amount,add_to_dlqueue=True)

    def wait_until_image_avalible(self,amount=1):
        """
        Wait until there's an image in the save folder.
        """
        while len(self.listdir()) < amount:
            if self.dlqueue.empty():
                raise Exception('No images planned for download, please run `get_images_ready` first')
    
    def get_current_image(self):
        return self.current_image,os.path.split(self.current_image)[1]
    
    def get_next_image(self):
        """
        Returns path and filename of next image.
        If there is no file, waits for download workers to download new ones.
        """
        self.wait_until_image_avalible(2)
        
        if self.current_image is not None:
            os.remove(self.current_image)
        self.current_image = random.choice(self.listdir())

        filename = os.path.split(self.current_image)[1]
        
        return self.current_image,filename
        

    def reset_session(self,new_session):
        """
        Removes all files in temp and downloads new ones.
        Also deletes unexpected images.
        """
        self.empty_dlqueue()
        
        for path in os.listdir(self.save_folder):
            os.remove(os.path.join(self.save_folder,path))

        return self.new_session(new_session)

    def new_session(self,session):
        """
        Gets new images ready, then picks a new current image
        """
        self.get_images_ready(*session)
        self.wait_until_image_avalible()
        
        self.current_image = None
        self.current_image = self.get_next_image()[0]
        
        return True
        