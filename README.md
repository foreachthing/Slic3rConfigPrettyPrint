# Slic3rConfigPrettyPrint
Prints the a Configuration-Report of a GCode File sliced with Slic3r

## REQUIRED
pdflatex (tested with TexLive 2018) or similar. Make adjustments in the script accordingly:
```
def runLaTeX():
 ...
    cmd = [ 'pdflatex', '-output-directory', dir_path2, '-interaction=nonstopmode', texfile] 
 ...
```

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
* `-cc|--commentcolor` changes the color of gcode comments (default: red)

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
