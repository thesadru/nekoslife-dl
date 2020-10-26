from nekoslife import NekosLife
import os

class NekosLifeTk(NekosLife):
    MAXIMUM_TRASH_FILES = 32
    current_image = None
    temp_copy_folder = '.temp/.trash'
    
    def __init__(self):
        super().__init__('.temp')
        
        if os.path.isdir(self.temp_copy_folder):
            self.temp_copies = [os.path.join(self.temp_copy_folder,i) for i in os.listdir(self.temp_copy_folder)]
        else:
            self.temp_copies = []
        
    
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
                files.append(i)
        
        return files
    
    def get_images_ready(self,imgtype: str, imgformat: str, imgcategory: str):
        """
        Downloads new images if less then half left.
        """
        if len(self.listdir()) < self.MAX_IMAGE_COUNT//2 and self.dlqueue.empty():
            urls = self.get_images(imgtype,imgformat,imgcategory)
            self.add_to_dlqueue(urls)
    
    def wait_until_image_avalible(self,amount=1):
        """
        Wait until there's an image in the save folder.
        """
        while len(self.listdir()) < amount:
            if self.dlqueue.empty():
                raise Exception('No images planned for download, please run `get_images_ready` first')
    
    def get_next_image(self):
        """
        Returns path and filename of next image.
        If there is no file, waits for download workers to download new ones.
        """
        self.wait_until_image_avalible(1)
        filename = self.listdir()[0]
        path = os.path.join(self.save_folder,filename)
        
        self.current_image = path
        
        return path,filename

    @staticmethod
    def move_file(file,nfolder):
        path = os.path.join(nfolder,os.path.split(file)[-1])
        if not os.path.exists(path):
            os.renames(file,path)
        else:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass # wtf, how I don't get it
        return path
        

    def delete_current_image(self):
        """
        places image in the trash
        """
        path = self.move_file(self.current_image,self.temp_copy_folder)
        
        if len(os.listdir(self.temp_copy_folder)) > self.MAXIMUM_TRASH_FILES:
            try:
                os.remove(self.temp_copies.pop(0))
            except FileNotFoundError:
                pass # wtf, how I don't get it
            
        self.temp_copies.append(path)
    
    def restore_previous(self):
        """
        restores last image from the trash
        """
        if len(self.temp_copies) == 0:
            return self.current_image
        last = self.temp_copies.pop(-1)
        path = self.move_file(last,self.save_folder)
        self.current_image = path
        return path
    
    def empty_trash(self):
        """
        Deletes trash
        """
        for path in self.temp_copies:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass # wtf, how I don't get it
    
    def move_current_image(self,dest):
        os.renames(self.current_image,dest)
    
    def reset_session(self,new_session):
        """
        Removes all files in temp and trash, the downloads new ones.
        """
        self.empty_trash()
        for path in self.listdir():
            os.remove(path)
        
        self.get_images_ready(*new_session)
        
        return True
        