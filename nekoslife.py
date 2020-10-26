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
    GET_URL = IMAGES_URL+"{t}/{f}/{c}/?count=%s" % MAX_IMAGE_COUNT
    # settings
    CHUNK_SIZE = 0x100000 # 1MibB
    ENDPOINT_TYPES = 'sfw','nsfw'
    ENDPOINT_FORMATS = 'img','gif'
    
    # variables
    dlqueue = Queue()
    endpoints = {}
    
    # imgpath = GET_URL.format(t='sfw',f='img',c='cat')
    
    def __init__(self, save_folder: str = 'images', download_threads: int = 1, generate_endpoints = True):
        ""
        self.save_folder = save_folder
        self._start_download_workers(download_threads)
        
        if not os.path.isdir(self.save_folder):
            os.makedirs(self.save_folder)
            
        if generate_endpoints:
            self.endpoints = self.get_endpoints()

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
        
        return endpoints

    def get_images(self,imgtype: str, imgformat: str, imgcategory: str):
        """
        Gets images from nekos.life, look at get_endpoints() to see all endpoints.
        Size of list is NekosLife.MAX_IMAGE_COUNT
        """
        url = self.GET_URL.format(t=imgtype,f=imgformat,c=imgcategory)
        r = requests.get(url)
        if r.status_code != 200:
            return []
        
        data = r.json()['data']
        urls = data['response']['urls']
        
        return urls

    def add_to_dlqueue(self,urls):
        """
        Adds urls to self.dlqueue.
        Uses methods should_enqueue(url_to_imagedata(url)) to check url validity.
        """
        for url in urls:
            urldata = self.url_to_imagedata(url)
            if self.should_enqueue(*urldata):
                self.dlqueue.put(urldata)
    
    def url_to_imagedata(self,url):
        """
        Returns url, filename, path
        """
        filename = os.path.split(url)[-1]
        path = os.path.join(self.save_folder,filename)
        
        return url,path,filename
    
    def should_enqueue(self,url,path,filename):
        """
        checks wheter a url should be enqueued
        """
        if os.path.exists(path):
            return False
        return True
    
    def add_images_to_dlqueue(self, imgtype: str, imgformat: str, imgcategory: str):
        """
        Gets images and appends them to the queue.
        Instead of using this function add_to_dlqueue(get_images()) is recommended.
        """
        urls = self.get_images(imgtype,imgformat,imgcategory)
        self.add_to_dlqueue(urls)

    def download_url(self,url,path,dlpath=None):
        """
        Downloads a file and saves it to path.
        """
        r = requests.get(url)
        if dlpath is None:
            dlpath = path
        with open(dlpath,'wb') as file:
            for chunk in r.iter_content(self.CHUNK_SIZE):
                file.write(chunk)
        os.rename(dlpath,path)

    def download_worker(self):
        """
        Gets urls from dlqueue and downloads them.
        """
        while True:
            url,path,filename = self.dlqueue.get()
            try:
                dlpath = path+'.000'
                self.download_url(url,path,dlpath)
            except (Exception,KeyboardInterrupt):
                if os.path.isfile(dlpath):
                    os.remove(dlpath)
            print(filename)
            self.dlqueue.task_done()
    
    def _start_download_workers(self,download_threads):
        self._download_workers = []
        for i in range(download_threads):
            t = threading.Thread(target=self.download_worker,name=f'nldlworker_{i}',daemon=True)
            t.start()
            self._download_workers.append(t)


if __name__ == "__main__":
    n = NekosLife()
    pprint(n.get_endpoints())