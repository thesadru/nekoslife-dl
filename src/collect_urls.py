from nekoslife_dl import NekosLife
import threading
from os.path import realpath,split,join
from os import makedirs

use_root = True

urls_folder = split(realpath(__file__))[0]
if use_root:
    urls_folder = split(urls_folder)[0]
urls_folder = join(urls_folder,'urls')

amount = 0xffffffff
expected_unique_leeway = 20

def generate_url_file(imgtype,imgformat,imgcategory=None):
    if imgcategory is not None:
        return join(urls_folder,imgtype,imgformat,imgcategory+'.txt')
    return join(urls_folder,imgtype,imgformat)

def create_dirs():
    for i in NekosLife.ENDPOINT_TYPES:
        for j in NekosLife.ENDPOINT_FORMATS:
            try:
                makedirs(generate_url_file(i,j))
            except FileExistsError:
                pass

def collect(imgtype,imgformat,imgcategory):
    nekoslife = NekosLife(
        "None",
        url_file = generate_url_file(imgtype,imgformat,imgcategory),
        sort_url_file = True
    )
    
    nekoslife.get_multiple_images(
        imgtype,imgformat,imgcategory,
        amount = amount,
        use_url_file = True,
        unique = amount,
        use_expected_unique = True,
        expected_unique_leeway = expected_unique_leeway
    )

def main():
    create_dirs()
    
    threads = []
    endpoints = NekosLife().get_endpoints()
    for imgtype in endpoints:
        for imgformat in endpoints[imgtype]:
            for imgcategory in endpoints[imgtype][imgformat]:
                t = threading.Thread(
                    target=collect,
                    name=f'cl_{imgtype}/{imgformat}/{imgcategory}',
                    args=(imgtype,imgformat,imgcategory),
                    daemon=True
                )
                t.start()
                threads.append(t)

    for i in range(len(threads)):
        threads[i].join()

if __name__ == "__main__":
    main()