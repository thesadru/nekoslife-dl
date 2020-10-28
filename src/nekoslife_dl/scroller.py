from .nekoslife import NekosLife
import os,time,random,threading

class NekosLifeScroller(NekosLife):
    """
    Allows scrolling through images from NekosLife.
    Basically how the API was actually intended to be used.
    
    Randomly gets a file from the `save_folder`.
    Needs a periodical download with `get_images_ready`
    """
    MAX_IMAGES = 60
    current_image = None
    get_thread = None
    
    def __init__(self,save_folder='.temp',*args,**kwargs):
        """
        Initializes the NekosLife class.
        Save folder is for the images, they will be deleted afterwards.
        """
        super().__init__(save_folder,*args,**kwargs)

        files = self.listdir()
        if len(files) > 0:
            self.current_image = files[0]
    
    def listdir(self):
        """
        Lists all files in savefolder.
        """
        files = []
        for i in os.listdir(self.save_folder):
            if os.path.splitext(i)[-1].endswith('.000'):
                continue
            path = os.path.join(self.save_folder,i)
            if os.path.isfile(path):
                files.append(path)
        
        return files

    def get_images_ready(self,imgtype: str, imgformat: str, imgcategory: str):
        """
        Downloads to fill `MAX_IMAGES`.
        For optimization downloads only when planned download would be more than `MAX_IMAGE_COUNT`.
        Returns (bool)success.
        """
        total_downloaded = len(self.listdir())+self.dlqueue.qsize()
        amount = self.MAX_IMAGES-total_downloaded
        
        if amount < self.MAX_IMAGE_COUNT:
            return False
        
        # new thread for optimization reasons
        if self.get_thread is None or not self.get_thread.is_alive():
            self.get_thread = threading.Thread(target=self.get_multiple_images,name='nldlgetter', daemon=True,
                args=(imgtype,imgformat,imgcategory,amount),kwargs={'add_to_dlqueue':True})
            self.get_thread.start()
        
        return True

    def wait_until_image_avalible(self,amount=1):
        """
        Wait until there's an image in the save folder.
        Remember to run `get_images_ready`, otherwise it will stall forever
        """
        while len(self.listdir()) < amount:
            pass # you could raise here
    
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
        self.wait_until_finished()
        
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
        