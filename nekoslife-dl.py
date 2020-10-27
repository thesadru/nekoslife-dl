from nekoslife import NekosLife
import argparse
import time

parser = argparse.ArgumentParser('nekoslife-dl')

parser.add_argument('type',choices=NekosLife.ENDPOINT_TYPES)
parser.add_argument('format',choices=NekosLife.ENDPOINT_FORMATS)
parser.add_argument('category')
parser.add_argument('save_folder',default='images')

parser.add_argument('--timeout',
    type=int,
    default=300,
    help='After what time the program stop downloading.')
parser.add_argument('--repeat',
    type=int,
    default=100,
    help='How many times to repeat getting images.')

parser.add_argument('-u','--url-folder',
    default=None,
    help='Saves data to a url folder instead of downloading.')
parser.add_argument('-r','--read-url-folder',
    action='store_true',
    help='Downloads from a url folder instead of writing to it.')

parser.add_argument('--threads',
    default=1,
    help='Amount of threads used for download')


args = parser.parse_args()
print(args)

nekoslife = NekosLife(args.save_folder, download_threads=args.threads)

endpoints = nekoslife.get_endpoints()
categories = endpoints[args.type][args.format]
if args.category not in categories:
    raise Exception('category must be in [%s]' % ','.join(categories))


start = time.time()

if args.url_folder is not None and args.read_url_folder:
    with open(args.url_folder,'r') as file:
        for url in file.readlines():
            url = url[:-1]
            urldata = nekoslife.url_to_imagedata(url)
            if nekoslife.should_enqueue(*urldata):
                nekoslife.dlqueue.put(urldata)
    
else:
    urls = set()
    for i in range(args.repeat):
        urls.update(nekoslife.get_images(args.type,args.format,args.category))

    if args.url_folder:
        with open(args.url_folder,'w') as file:
            file.write('\n'.join(urls))
    else:
        nekoslife.add_to_dlqueue(urls)

print(urls)
print('GOT ALL URLS, NOW ONLY DOWNLOADING')
while time.time()-start < args.timeout:
    pass