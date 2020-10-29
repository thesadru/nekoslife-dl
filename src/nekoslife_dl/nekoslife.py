"""
The main nekoslife file
Contains NekosLife, the main class
"""
import json
import os
import threading
import time
from pprint import pprint
from queue import Queue
import requests
from nekoslife_dl.errors import IllegalCategoryError


class NekosLife:
    """
    Downloads data from nekos.life.
    Uses https://api.nekos.dev/api/v3/.
    Since there is no offical API for v3, I made one myself.

    It gets images using the API, then adds them into `dlqueue`.
    Download workers will then download it.

    For the simplest behaviour you can use this
    ```
    from nekoslife import NekosLife
    nekoslife = NekosLife(...)
    nekoslife.get_multiple_images(...,add_to_dlqueue=True)
    nekoslife.wait_until_finished()
    ```
    """

    # constants
    MAX_IMAGE_COUNT = 20  # 20 is currently max
    # urls
    URL = "https://api.nekos.dev/api/v3/"
    IMAGES_URL = URL+'images/'
    GET_URL = IMAGES_URL+"{t}/{f}/{c}/?count={a}"
    CDN_URL = "https://cdn.nekos.life/v3/{t}/{f}/{c}/{i}"

    PROGRESS_BAR = "\r[*] {d} / {u} images [{t} / {e}]"+' '*6
    start_dl_time = time.time()
    estimated_time = 0

    # settings
    CHUNK_SIZE = 0x100000  # 1MibB
    ENDPOINT_TYPES = 'sfw', 'nsfw'
    ENDPOINT_FORMATS = 'img', 'gif'
    SHOW_PROGRESS_BAR = False
    SORT_URL_FILE = False

    # variables
    dlqueue = Queue()
    endpoints = {}

    save_folder = None
    url_file = None

    def __init__(self,
        save_folder: str = 'images', download_threads: int = 1,
        progress_bar: bool = False,
        url_file: str = None, sort_url_file: bool = False,
        generate_endpoints: bool = False):
        """
        `save_folder` is the path to downloaded images.
        `download_threads` initializes the set amount of `download workers`.
        `progress_bar` shows a progress bar for downloading (shows progress and estimated time).
        Essentially a quiet tag.
        `url_file` is used to store all gotten urls.
        You can use it without downloading and then later automatically add all the urls.
        `sort_url_file` sorts the url file and prevents duplicates.
        `generate_endpoints` generates endpoints when initializing so you don'thave to wait later.
        """
        self.save_folder = save_folder
        self.url_file = url_file

        if not os.path.isdir(self.save_folder):
            os.makedirs(self.save_folder)

        self.SHOW_PROGRESS_BAR = progress_bar
        self.SORT_URL_FILE = sort_url_file

        if generate_endpoints:
            self.get_endpoints()

        self._start_download_workers(download_threads)

    # =========================================================================
    # get images

    def get_images(self, imgtype: str, imgformat: str, imgcategory: str, amount: int = None):
        """
        Gets images from nekos.life, look at `get_endpoints()` to see all endpoints.
        Size of list is `amount`, `MAX_IMAGE_COUNT` by default.
        Returns `(int)status_code` if status code is not 200.
        """
        if amount == 0:
            amount = self.MAX_IMAGE_COUNT
        elif amount == 0:
            return 0

        url = self.generate_image_url(imgtype, imgformat, imgcategory)
        r = requests.get(url)
        if r.status_code != 200:
            return r.status_code

        data = r.json()['data']
        if not data['status']['success']:
            raise IllegalCategoryError(
                'You must supply a proper category, check endpoints.')
        urls = data['response']['urls']

        return urls

    def get_multiple_images(self,
            imgtype: str, imgformat: str, imgcategory: str, amount: int,
            add_to_dlqueue: bool = False,
            use_url_file=False,
            unique: int = 0):
        """
        Gets multiple images than is allowed by the API.
        If `add_to_dlqueue` is True, starts adding all the urls to dlqueue,
        If `use_url_file`, undownloaded urls will be downloaded and at the end of getting saved.
        If `unique` is <= 0, a list with random urls will be returned or lenght amount.
        Else a set of lenght:`lenght <= unique ± MAX_IMAGE_COUNT` will be returned.
        """
        if use_url_file:
            urls = self.get_urls_file()
            if add_to_dlqueue:
                self.add_to_dlqueue(urls)
        else:
            urls = []

        if unique <= 0:
            for i in self._number_split(amount, self.MAX_IMAGE_COUNT):
                new_urls = self.get_images(imgtype, imgformat, imgcategory, i)
                urls.extend(new_urls)

                if add_to_dlqueue:
                    self.add_to_dlqueue(new_urls)
                self.print_progress_bar()

        else:
            urls = set(urls)
            for i in self._number_split(amount, self.MAX_IMAGE_COUNT):
                new_urls = self.get_images(imgtype, imgformat, imgcategory, i)
                new_urls = set(new_urls).difference(urls)
                urls.update(new_urls)

                if add_to_dlqueue:
                    self.add_to_dlqueue(new_urls)
                self.print_progress_bar()

                if len(urls) >= unique:
                    break

        if use_url_file:
            self.add_urls_file(set(urls))

        return urls

    # =========================================================================
    # download

    def add_to_dlqueue(self, urls):
        """
        Adds urls to `dlqueue`.
        Uses methods `should_enqueue(url_to_imagedata(url))` to check url validity.
        If you want to guarantee that there's no copies, pass in a set.
        """
        for url in urls:
            urldata = self.url_to_imagedata(url)
            if self.should_enqueue(*urldata):
                self.dlqueue.put(urldata)

    def url_to_imagedata(self, url):
        """
        Converts a url to `(url, filename, path)`.
        """
        filename = os.path.split(url)[-1]
        path = os.path.join(self.save_folder, filename)

        return url, path, filename

    def should_enqueue(self, url, path, filename):
        """
        Checks wheter a url should be enqueued.
        Valid if file does not exist.
        """
        if os.path.exists(path):
            return False
        return True

    def wait_until_finished(self, timeout=60*60):
        """
        Waits until all downloads are finished.
        Returns True when everything was downloaded.
        If you want no timeout, `dlqueue.join()` is better, but it doesn't allow KeyboardInterrupt.
        """
        start = time.time()
        while self.dlqueue.unfinished_tasks:
            if time.time() - start > timeout:
                return False

        return True

    # =========================================================================
    # download workers

    def download_url(self, url, path, dlpath=None, special_filename=None):
        """
        Downloads a file and saves it to path.
        Dlpath will be the file path while still downloading.
        Returns how long the download took. 0 if failed.
        `special_filename` has no usage currently.
        """
        start = time.time()
        r = requests.get(url)
        if dlpath is None:
            dlpath = path
        with open(dlpath, 'wb') as file:
            for chunk in r.iter_content(self.CHUNK_SIZE):
                file.write(chunk)
        os.rename(dlpath, path)

        return time.time() - start

    def download_worker(self):
        """
        Gets urls from `dlqueue` and downloads them.
        Updates the estimated time and prints progress bar every download.
        """
        while True:
            url, path, filename = self.dlqueue.get()

            try:
                dlpath = path+'.000'
                dl_time = self.download_url(url, path, dlpath, filename)
                self.update_estimated_time(dl_time)
            except (Exception, KeyboardInterrupt):
                if os.path.isfile(dlpath):
                    os.remove(dlpath)

            self.print_progress_bar()
            self.dlqueue.task_done()

    def _start_download_workers(self, amount):
        """
        Starts a set amount of download workers.
        Remember to run this function only once.
        """
        self._download_workers = []
        for i in range(amount):
            t = threading.Thread(target=self.download_worker,
                                 name=f'nldlworker_{i}', daemon=True)
            t.start()
            self._download_workers.append(t)

    # =========================================================================
    # url file

    def get_urls_file(self):
        """
        Gets all urls from `url_file`. Urls must be seperated by `\\n`.
        """
        if self.url_file is None or not os.path.isfile(self.url_file):
            return []

        urls = []
        with open(self.url_file, 'r') as file:
            for url in file.readlines():
                if len(url) > 1:
                    url = url.strip('\n')
                    urls.append(url)
        return urls

    def set_urls_file(self, urls):
        """
        Sets the content of the `url_file` into urls.
        """
        if self.url_file is None:
            return []

        with open(self.url_file, 'w') as file:
            if self.SORT_URL_FILE:
                urls = sorted(urls, key=self.url_index)
            file.write('\n'.join(urls))
        return urls

    def add_urls_file(self, urls):
        """
        Adds urls into `url_file`.
        """
        return self.set_urls_file(set(urls).union(self.get_urls_file()))

    # =========================================================================
    # progress bar

    def print_progress_bar(self):
        """
        Prints the progress bar.
        When `SHOW_PROGRESS_BAR` is False, doesn't print.
        Time may go up and down if the CPU is slow.
        """
        if not self.SHOW_PROGRESS_BAR:
            return False

        downloaded_urls = len(os.listdir(self.save_folder))
        planned_urls = self.dlqueue.qsize()
        urls = downloaded_urls + planned_urls
        current_time = round(time.time()-self.start_dl_time, 2)
        estimated_time = round(current_time+self.estimated_time*planned_urls, 2)

        print(
            self.PROGRESS_BAR.format(
                d=downloaded_urls, u=urls,
                t=self._to_minutes(current_time), e=self._to_minutes(estimated_time)),
            end=''
        )
        return True

    def update_estimated_time(self, time):
        """
        Updates estimated time of seconds per image.
        Should only be used internally.
        """
        if self.estimated_time is None:
            self.estimated_time = time
        else:
            urls = len(os.listdir(self.save_folder))
            self.estimated_time = (urls*self.estimated_time+time)/(urls+1)

    # =========================================================================
    # static methods

    @staticmethod
    def _to_minutes(seconds):
        """
        Progress bar tool that converts seconds into a `?min ?s` format
        """
        minutes, seconds = map(int, divmod(seconds, 60))
        if minutes == 0:
            return f'{seconds}s'
        else:
            return f'{minutes}min {seconds}s'

    @staticmethod
    def url_index(url):
        """
        Gets the number in the image filename.
        Useful for sorting or guessing missing images.
        """
        filename = os.path.split(url)[1]
        number = ''
        for i in filename:
            if i.isdigit():
                number += i
        return int(number)

    @staticmethod
    def _number_split(n, s):
        """
        Splits n into a sorted array a of integers x, 
        where x <= s and the lenght of a is the smallest possible.
        """
        if n == 0:
            return ()
        i = 0
        for i in range(s, n, s):
            yield s
        yield n-i

    # =========================================================================
    # utility

    def generate_image_url(self, imgtype, imgformat, imgcategory, amount=None):
        """
        Generates url to get images.
        """
        if amount is None:
            amount = self.MAX_IMAGE_COUNT

        if not (2 <= amount <= self.MAX_IMAGE_COUNT):
            raise ValueError(
                f'Amount must be 2 < amount <= {self.MAX_IMAGE_COUNT}.')

        url = self.GET_URL.format(
            t=imgtype, f=imgformat, c=imgcategory, a=amount)
        if amount > 2:
            return url
        else:
            return url[:8]

    def get_endpoints(self, force=False) -> dict:
        """
        Gets all endpoints by requesting bad urls and getting corrected.
        If endpoints have been already once generated, returns the old endpoints.
        To overcome this use `force`.
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

    def raise_for_category(self, imgtype, imgformat, imgcategory):
        """
        Raises ValueError if category is invalid.
        """
        if imgtype not in self.ENDPOINT_TYPES:
            raise IllegalCategoryError('type must be in [%s]'
                             % ','.join(self.ENDPOINT_TYPES))
        if imgformat not in self.ENDPOINT_FORMATS:
            raise IllegalCategoryError('format must be in [%s]'
                             % ','.join(self.ENDPOINT_FORMATS))

        endpoints = self.get_endpoints()[imgtype][imgformat]
        if imgcategory not in endpoints:
            raise IllegalCategoryError(f'category for {imgtype}/{imgformat} must be in [%s]'
                             % ','.join(endpoints))

    def empty_dlqueue(self):
        """
        Marks all unstarted tasks as done.
        """
        while not self.dlqueue.empty():
            self.dlqueue.get()
            self.dlqueue.task_done()


if __name__ == "__main__":
    help(NekosLife)
