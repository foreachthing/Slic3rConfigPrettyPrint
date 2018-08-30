# Slic3rConfigPrettyPrint
Prints the a Configuration-Report of a GCode File sliced with Slic3r

## REQUIRED
pdflatex (tested with TexLive 2018) or similar. Make adjustments in the script accordingly:
```
def runLaTeX():
    cmd = ['pdflatex', '-interaction', 'nonstopmode', tplout.name]
```

## Usage
Just run the script with your GCode-file as first parameter. I.e. `PROG mySlicedFile.gcode`

Use these, optional, parameters:
* -b removes the graphic representation of the bed shape
* -t removes the text (xy coordinates) of the bed shape
* -bt removes the bed shape completely

Input: `PROG  mySlicedFile.gcode -t`
Output: PDF with graphic of bed shape, no xys'.


Edit `LaTexTemplate()` to match your usual layout.
Style is in `LaTexStyle()`.


## Preview
### Summary
![preview](https://raw.githubusercontent.com/foreachthing/Slic3rConfigPrettyPrint/master/preview.png)

### Bed shape
![preview](https://raw.githubusercontent.com/foreachthing/Slic3rConfigPrettyPrint/master/preview2.png)
