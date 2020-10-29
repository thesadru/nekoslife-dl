# nekoslife-dl
A wrapper for nekos.life. Allows download and browsing.
<div align="center">
  ![GitHub](https://img.shields.io/github/license/thesadru/nekoslife-dl)
  ![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/thesadru/nekoslife-dl)
  ![GitHub last commit](https://img.shields.io/github/last-commit/thesadru/nekoslife-dl)
  ![GitHub Release](https://img.shields.io/github/v/release/thesadru/nekoslife-dl?include_prereleases)
</div>

# what's this project
This project allows download from [nekos.life](https://nekos.life). Since the only avalible projects use api v2, I made my own that uses v3. It also allows viewing images.

# how to use the library
Either install with pip or place `src/nekoslife_dl` in your project. Then import from `nekoslife_dl`. The main module is `NekosLife`. The script should have enough comments, so you should be able to guess what's happening.

# how to use the tools
## nekoslife-dl
run `python src/nekoslife-dl --help`. The documentation should print.
## tkscroller
run `python src/tkscroller`. Then press the right arrow key to scroll to the next image. You can pick different images with the OptionMenus on top
## tksorter
run `python src/tksorter TRASHKEYSYM [KEYS]`. `TRASHKEYSYM` should be a symbol of a key that wil delete the current image, other keys will be in pairs like this: `KEYSYM DIRECTORY`.
Example: `python .\src\tksorter.py Right z "images/liked" x "images/decent"`

# TODO
- code optimizations
- viewing on web
