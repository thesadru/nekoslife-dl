from nekoslife_dl import NekosLife
import argparse
import time
__doc__ = """
Downloads images from https://nekos.life.
Has a progress bar and multi-threaded download.
"""
parser = argparse.ArgumentParser('nekoslife-dl',description=__doc__)

parser.add_argument('type',choices=NekosLife.ENDPOINT_TYPES)
parser.add_argument('format',choices=NekosLife.ENDPOINT_FORMATS)
parser.add_argument('category')
parser.add_argument('-q','--quiet',
    action='store_true',
    help="Does not show the progress bar."
)

download = parser.add_argument_group('download')
download.add_argument('-a','--amount',
    type=int,
    default=20,
    help="Amount of images to try and download."
)
download.add_argument('-u','--unique',
    type=int,
    default=0,
    help="Amount of unique images to download,\
          when <= 0, the program downloads images and doesn't care about duplicates."
)
download.add_argument('--timeout',
    type=int,
    default=60*60,
    help="How many seconds to wait until release lock, if download is taking too long."
)
download.add_argument('-c','--autocomplete','--complete',
    action='store_true',
    help="Autocompletes the missing images. Fairly slow since it has to test multiple urls."
)

paths = parser.add_argument_group('paths')
paths.add_argument('-f','--folder',
    default='images',
    help="Where to save all the images."
)
paths.add_argument('-F','--url-file',
    default=None,
    help="Uses a file to store all gotten urls. Can later read from it to save time.\
          They will be added only after url collecting ends."
)

utility = parser.add_argument_group('utility')
utility.add_argument('--threads',
    type=int,
    default=1,
    help="How many threads will be used to download images."
)
utility.add_argument('--sort-url-file',
    action='store_true',
    help="Sorts urls in the url file. No functionality."
)
utility.add_argument('--update-file-every-url',
    action='store_true',
    help="Adds a url every autocomplete, causes performance issues."
)


args = parser.parse_args()

nekoslife = NekosLife(
    args.folder, download_threads = args.threads, 
    progress_bar = not args.quiet,
    url_file = args.url_file, sort_url_file = args.sort_url_file)
nekoslife.raise_for_category(args.type,args.format,args.category)

urls = nekoslife.get_multiple_images(
    args.type,args.format,args.category,
    amount = args.amount,
    add_to_dlqueue = True,
    use_url_file = args.url_file is not None,
    unique = args.unique)

if args.autocomplete:
    nekoslife.autocomplete_urls(self,
        urls,
        add_to_dlqueue=True,
        use_url_file=args.url_file is not None,
        update_file_every_url=args.update_file_every_url)

nekoslife.wait_until_finished(args.timeout)