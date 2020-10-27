from nekoslife import NekosLife
import os,time

class NekosLifeScroller(NekosLife):
    MAX_HISTORY_LEN = 32
    file_tracker = []
    file_tracker_ptr = 0 # points at current position
    
    def __init__(self):
        super().__init__('.temp')

        file_tracker = self.listdir()
    
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
    
    @property
    def current_image(self):
        return self.file_tracker[self.file_tracker_ptr]

    def get_planned_images(self):
        """
        Returns amount of images that are downloaded (planned for download).
        """
        return len(self.file_tracker) - self.file_tracker_ptr
    
    def delete_unused_images(self):
        if self.file_tracker_ptr > self.MAX_HISTORY_LEN:
            os.remove(self.file_tracker[-1])
            self.file_tracker_ptr -= 1

    def put_into_dlqueue(self,urldata):
        self.file_tracker.append(urldata[1]) #path
        self.delete_unused_images()
        self.dlqueue.put(urldata)

    def get_images_ready(self,imgtype: str, imgformat: str, imgcategory: str):
        """
        Downloads new images if less then half left.
        """
        if self.get_planned_images() < self.MAX_IMAGE_COUNT//2:
            urls = self.get_images(imgtype,imgformat,imgcategory)
            self.add_to_dlqueue(urls)

    def get_downloaded(self):
        """
        Returns all downloaded images, deletes unexpected ones.
        """
        a = set(self.file_tracker)
        b = self.listdir()
        a.

        return

    def wait_until_image_avalible(self,amount=1):
        """
        Wait until there's an image in the save folder.
        """
        while len(self.listdir()) < amount:
            if self.get_planned_images() < amount:
                raise Exception('No images planned for download, please run `get_images_ready` first')

    def get_next_image(self):
        """
        Returns path and filename of next image.
        If there is no file, waits for download workers to download new ones.
        """
        self.wait_until_image_avalible(1)
        self.file_tracker_ptr += 1
        
        filename = os.path.split(self.current_image)[1]

        return filename,self.current_image

    def reset_session(self,new_session):
        """
        Removes all files in temp and trash, the downloads new ones.
        """
        for path in self.file_tracker:
            os.remove(path)

        file_tracker_ptr = 0
        
        self.get_images_ready(*new_session)
        
        return True