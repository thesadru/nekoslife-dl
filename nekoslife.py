import json
import os
import threading
import time
from pprint import pprint
from queue import Queue

import requests

class NekosLife:
    """
    Downloads data from nekos.life.
    Uses https://api.nekos.dev/api/v3/.
    Since there is no offical API for v3, I made one myself.
    """
    
    # constants
    MAX_IMAGE_COUNT = 20 # 20 is currently max
    # urls
    URL = "https://api.nekos.dev/api/v3/"
    IMAGES_URL = URL+'images/'
    GET_URL = IMAGES_URL+"{t}/{f}/{c}/?count={a}"
    
    PROGRESS_BAR = "\r[*] {d} / {u} images [{t}s / {e}s]"+' '*6
    start_dl_time = time.time()
    estimated_time = 0
    
    # settings
    CHUNK_SIZE = 0x100000 # 1MibB
    ENDPOINT_TYPES = 'sfw','nsfw'
    ENDPOINT_FORMATS = 'img','gif'
    SHOW_PROGRESS_BAR = False
    
    # variables
    dlqueue = Queue()
    endpoints = {}
    
    # imgpath = GET_URL.format(t='sfw',f='img',c='cat')
    
    def __init__(self,
            save_folder: str = 'images', download_threads: int = 1, 
            progress_bar: bool = False,
            generate_endpoints = False):
        ""
        self.save_folder = save_folder
        
        if not os.path.isdir(self.save_folder):
            os.makedirs(self.save_folder)
        
        self.SHOW_PROGRESS_BAR = progress_bar
        
        if generate_endpoints:
            self.get_endpoints()
        
        self._start_download_workers(download_threads)
            
    def generate_image_url(self,imgtype,imgformat,imgcategory,amount=None):
        """
        Generates url to get images.
        """
        if amount is None:
            amount = self.MAX_IMAGE_COUNT
        
        if not (0 < amount <= self.MAX_IMAGE_COUNT):
            raise ValueError(f'Amount must be 0 < amount <= {self.MAX_IMAGE_COUNT}.')
        
        return self.GET_URL.format(t=imgtype,f=imgformat,c=imgcategory,a=amount)

    def get_endpoints(self,force=False) -> dict:
        """
        Gets all endpoints by requesting bad urls and getting corrected.
        """
        if self.endpoints and not force:
            return self.endpoints
        
        endpoints = {}
        for i in self.ENDPOINT_TYPES:
            endpoints[i] = {}
            for j in self.ENDPOINT_FORMATS:
                url = self.IMAGES_URL+i+'/'+j+'/'
                data = requests.get(url).json()['data']
                endpoints[i][j] = data['response']['categories']
        
        self.endpoints = endpoints
        
        return endpoints
    
    def print_progress_bar(self):
        if not self.SHOW_PROGRESS_BAR:
            return False
        
        downloaded_urls = len(os.listdir(self.save_folder))
        planned_urls = self.dlqueue.qsize()
        urls = downloaded_urls + planned_urls
        current_time = round(time.time()-self.start_dl_time, 2)
        estimated_time = round(current_time+self.estimated_time*planned_urls, 2)
        
        print(
            self.PROGRESS_BAR.format(
                d=downloaded_urls,u=urls,t=current_time,e=estimated_time),
            end=''
        )
        return True
    
    def update_estimated_time(self,time):
        """
        Updates estimated time of seconds per image.
        """
        if self.estimated_time is None:
            self.estimated_time = time
        else:
            urls = len(os.listdir(self.save_folder))
            self.estimated_time = (urls*self.estimated_time+time)/(self.estimated_time+1)

    def get_images(self,imgtype: str, imgformat: str, imgcategory: str, amount: int = None):
        """
        Gets images from nekos.life, look at `get_endpoints()` to see all endpoints.
        Size of list is amount, `MAX_IMAGE_COUNT` by default.
        Returns `(int)status_code` if status code is not 200.
        """
        if amount == 0:
            amount = self.MAX_IMAGE_COUNT
        elif amount == 0:
            return 0
        
        url = self.generate_image_url(imgtype,imgformat,imgcategory)
        r = requests.get(url)
        if r.status_code != 200:
            return r.status_code
        
        data = r.json()['data']
        urls = data['response']['urls']
        
        return urls
    
    @staticmethod
    def _number_split(n,s):
        """
        Splits n by every s.
        """
        if n == 0:
            return ()
        i = 0
        for i in range(s,n,s):
            yield s
        yield n-i
    
    def get_multiple_images(self,
            imgtype: str, imgformat: str, imgcategory: str, amount: int, 
            add_to_dlqueue: bool = False,
            minimum_unique: int = 0):
        """
        Gets multiple images than is allowed by the API.
        If `add_to_dlqueue` is True, starts adding all the urls to dlqueue,
        If `minimum_unique` is <= 0, a list with random urls will be returned or lenght amount.
        Else a set of `lenght <= mimumum_unique ± MAX_IMAGE_COUNT` will be returned.
        """
        if minimum_unique <= 0:
            urls = []
            for i in self._number_split(amount,self.MAX_IMAGE_COUNT):
                new_urls = self.get_images(imgtype,imgformat,imgcategory,i)
                urls.extend(new_urls)
                
                if add_to_dlqueue:
                    self.add_to_dlqueue(new_urls)
                self.print_progress_bar()
        
        else:
            urls = set()
            for i in self._number_split(amount,self.MAX_IMAGE_COUNT):
                new_urls = self.get_images(imgtype,imgformat,imgcategory,i)
                new_urls = set(new_urls).difference(urls)
                urls.update(new_urls)
                
                if add_to_dlqueue:
                    self.add_to_dlqueue(new_urls)
                self.print_progress_bar()
                
                if len(urls) >= minimum_unique:
                    break
        return urls
    
    def add_to_dlqueue(self,urls):
        """
        Adds urls to `dlqueue`.
        Uses methods `should_enqueue(url_to_imagedata(url))` to check url validity.
        """
        for url in urls:
            urldata = self.url_to_imagedata(url)
            if self.should_enqueue(*urldata):
                self.dlqueue.put(urldata)
    
    def url_to_imagedata(self,url):
        """
        Converts a url to `(url, filename, path)`.
        """
        filename = os.path.split(url)[-1]
        path = os.path.join(self.save_folder,filename)
        
        return url,path,filename
    
    def should_enqueue(self,url,path,filename):
        """
        Checks wheter a url should be enqueued.
        """
        if os.path.exists(path):
            return False
        return True
        
    def empty_dlqueue(self):
        """
        Marks all tasks unstarted tasks as done.
        """
        while not self.dlqueue.empty():
            self.dlqueue.get()
            self.dlqueue.task_done()
    
    def wait_until_finished(self,timeout=60*60):
        """
        Waits until all downloads are finished.
        Returns True when everything was downloaded.
        If you want no timeout, `dlqueue.join()` is better.
        """
        start = time.time()
        while self.dlqueue.unfinished_tasks:
            if time.time() - start > timeout:
                return False
        
        return True
                

    def download_url(self,url,path,dlpath=None):
        """
        Downloads a file and saves it to path.
        Dlpath will be the file path while still downloading.
        Returns how long the download took. 0 if failed
        """
        start = time.time()
        r = requests.get(url)
        if dlpath is None:
            dlpath = path
        with open(dlpath,'wb') as file:
            for chunk in r.iter_content(self.CHUNK_SIZE):
                file.write(chunk)
        os.rename(dlpath,path)
        
        return time.time() - start

    def download_worker(self):
        """
        Gets urls from `dlqueue` and downloads them.
        """
        while True:
            url,path,filename = self.dlqueue.get()
            
            try:
                dlpath = path+'.000'
                dl_time = self.download_url(url,path,dlpath)
                self.update_estimated_time(dl_time)
            except (Exception,KeyboardInterrupt):
                if os.path.isfile(dlpath):
                    os.remove(dlpath)
            
            self.print_progress_bar()
            self.dlqueue.task_done()
    
    def _start_download_workers(self,download_threads):
        self._download_workers = []
        for i in range(download_threads):
            t = threading.Thread(target=self.download_worker,name=f'nldlworker_{i}',daemon=True)
            t.start()
            self._download_workers.append(t)


if __name__ == "__main__":
    n = NekosLife(download_threads=2,progress_bar=True)
    urls = n.get_multiple_images('sfw','img','cat',10,add_to_dlqueue=True,minimum_unique=0)
    n.wait_until_finished()
    