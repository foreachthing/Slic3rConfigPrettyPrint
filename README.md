# Slic3rConfigPrettyPrint
Prints the a Configuration-Report of a GCode File sliced with Slic3r.

## REQUIRED
### Latex
* pdflatex or similar (xelatex may work). Make adjustments in the script accordingly:
```
def runLaTeX():
 ...
    cmd = [ 'pdflatex', '-output-directory', dir_path2, '-interaction=nonstopmode', texfile] 
 ...
```
Required packages:
* scrlayer-scrpage
* environ
* hyperref
* inputenc
* fontenc
* lmodern
* geometry
* booktabs
* ltablex
* siunitx
* menukeys
* caption
* marginnote
* titletoc

Additional packges on Debian-Jessie required (~ 550 MB):
* xstring 
* etoolbox
* adjustbox
* collectbox
* relsize
* trimspaces
* l3kernel



### Python
Written in Python 3.7. Maybe earlier version will work too.
Required packages:
* os 
* sys
* pathlib
* re 
* argparse
* subprocess

### Tested with
* Windows 7 (x64)
* Windows 8.1 (x64)
* Ubunut 16.04 LTS
* TexLive 2018 (full install)
* MikTex 2.9 (auto install missing packages)

## Usage
Just run the script with your GCode-file as first parameter. I.e. `PROG mySlicedFile.gcode`

Use these, optional, parameters:
* `-au|--author` define the author of the pdf
* `-b` removes the graphic representation of the bed shape
* `-t` removes the text (xy coordinates) of the bed shape
* `-bt` removes the bed shape completely
* `-g` removes all gcode sections
* `-c` prints the configuration section only
* `-s` prints the summary section only (cannot be used with `-c`)
* `-cc|--commentcolor` changes the color of gcode comments, in hex (default: ff0000 = red)

## Usage in Slic3r
If you want to use this script as a post-processor (create a pdf automatically with exporting gcode) then use this script as following:
`C:\Program! Files! (x86)\Python37-32\python.exe c:\dev\SCPP\Slic3rConfigPrettyPrint.py -o --au "John Doe"`

Make sure you don't have a white-space at the end of this string. Otherwise you'll get a syntax error.
NOTE: before every white-space you'll need an **!**. Whatch closly: `C:\Program! Files! (x86)\`.

## Examples
Input: `PROG  mySlicedFile.gcode -t -au "Mister Slic3r"`

Output: PDF with graphic of bed shape, no xys. Change the author name to "Mister Slic3r".

Input: `PROG  mySlicedFile.gcode -c -cc dd0034`

Output: PDF without the summary and comments colors in dd0034'.

## Customize
Edit `LaTexTemplate()` to match your usual layout.
Style is in `LaTexStyle()`.


## Preview
### Summary
![preview](https://raw.githubusercontent.com/foreachthing/Slic3rConfigPrettyPrint/master/preview.png)

### Bed shape
![preview](https://raw.githubusercontent.com/foreachthing/Slic3rConfigPrettyPrint/master/preview2.png)
