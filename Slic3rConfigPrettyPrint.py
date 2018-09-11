#!/usr/bin/python

#TODO:
# Filament usage in Meter

import os 
from os import path
import sys
import pathlib
from pathlib import Path
import re  #regex
import argparse
import subprocess

# Debug only
#print(sys.argv)


## ArgumentParser
parser = argparse.ArgumentParser(
    prog = os.path.basename(__file__),
    description = 'Change the option prefix characters', 
    prefix_chars = '-+/',
    epilog = '', )

parser.add_argument('filename', nargs = '?', help = 'Filename (GCode-File) to process.')
parser.add_argument('-au', '--author', metavar = '"Author Name"', default = os.getenv('username').title(), help = 'The Author of the GCode-File (default: %(default)s)')
#
grpDisable = parser.add_argument_group('Disable printing of ...', 'Note: -b and -t can be combined as -bt or -tb.')
grpDisable.add_argument('-b', action = 'store_false', default = True, help = 'Bed Shape as graphic')
grpDisable.add_argument('-t', action = 'store_false', default = True, help = 'Bed Shape as text (xy coordinates)')
grpDisable.add_argument('-g', action = 'store_false', default = True, help = 'Removes all GCode fields (start, end, filament, layer, etc.)')

#
group = parser.add_mutually_exclusive_group()
group.add_argument('-c', action = 'store_true', default = False, help = 'Print configuration section only')
group.add_argument('-s', action = 'store_true', default = False, help = 'Print summary section only')

parser.add_argument("-cc", "--commentcolor", action='store', type=str, metavar = 'hex', default = 'ff0000',  help = 'Font color of comments in HEX (default: %(default)s without leading #)')
parser.add_argument('-o', action = 'store_true', default = False, help = 'Open PDF after creation.')


if not len(sys.argv) > 1:
    print('\n\n*** WARNING ***\nNo Parameter(s) provided but at least one (GCode-filename) required. \n*** Type "[PROG_NAME] -h" for help ***\nI shall exit here.')
    exit(1)
try:
    args = parser.parse_args()
except IOError as msg:
    parser.error(str(msg))

strAuthor           = args.author
bbed_shape          = args.b
bSection_Config     = args.c
bgcode_fields       = args.g
bOpenPDF            = args.o
bSection_Summary    = args.s
bbed_shapetxt       = args.t
filename            = Path(str(args.filename))
strFontCommentColor = args.commentcolor

## END ArgumentParser

## get and set paths
dir_path = Path(filename).parents[0] 
pdfname = (Path(filename).stem)


# define output files
out = open(dir_path/'slic3rconfigtable.tex','w')
outputconfig = Path(str(out.name))
 # Summary
summ = open(dir_path/'slic3rsummary.tex','w')
outputsummary = Path(str(summ.name))
 # Bedshape
bedshp = open(dir_path/'slic3rbedshape.data','w')
outputbedshape = Path(str(bedshp.name))
 # Main TEX file
tplout = open(dir_path/(pdfname+'.tex'),'w')
outputtplout = Path(str(tplout.name))
 # Main Style file
styout = open(dir_path/'GCodeSuperStylin.sty','w')
outputstyle = Path(str(styout.name))

# global vars for grid in bed shape
gridxmin = float(0)
gridxmax = float(0)
gridymin = float(0)
gridymax = float(0)

def main():

    # if no file specified, exit! If it comes to that ...
    if str(filename).lower() == 'none':
        print('No Parameter for "filename" provided. I shall exit here.')
        exit(1)
      
    myGCODEfile = open(filename, 'r')
    mylines = myGCODEfile.readlines()
    myGCODEfile.close()

    # main list
    lstCompleteNewLines=list()
        
    try:    
        strFirstLine = mylines[0] # Slic3r Info      

        # reverse it and stop at the first empty line
        mylines.reverse()

        for strLine in mylines:

            if strLine.startswith('\n'):
                break
            if '\n' in strLine:
                strLine = rn(strLine)
            if '\\n' in strLine and not strLine.endswith('\n'):
                strLine = strLine.replace('\\n',' \\n ')

            strLine=strLine.replace('; ','',1) # replace only first occurence

            ## Some more replacements for LaTeX
            strLine = strLine.replace('%','\\%')
            strLine = strLine.replace('#','\\#')
            strLine = strLine.replace('[','{[')
            strLine = strLine.replace(']',']}')
 
            lowline = strLine.lower()

            if lowline.startswith('start_gcode') or lowline.startswith('end_gcode') or lowline.startswith('between_objects_gcode') or lowline.startswith('layer_gcode') or lowline.startswith('before_layer_gcode') or lowline.startswith('post_process') or lowline.startswith('bed_shape') or lowline.startswith('notes') or lowline.startswith('printer_notes') or lowline.startswith('filament_notes'):
                if (bgcode_fields == False):
                    
                    if lowline.startswith('start_gcode') or lowline.startswith('end_gcode') or lowline.startswith('between_objects_gcode') or lowline.startswith('layer_gcode') or lowline.startswith('before_layer_gcode'):
                        #print('no gcode please')
                        continue
                    else:
                        processGCodeLines(strLine, lowline, lstCompleteNewLines)
                        continue

                else:
                    #print('more gcode')
                    # SUB HERE
                    processGCodeLines(strLine, lowline, lstCompleteNewLines)
                    continue

            spline = strLine.split('=')

            strFirst = spline[0].title().replace('_',' ')
            strSecond = LaTeXStringFilter(spline[1])


            # print("Option:  {0:50}   Value:  {1}".format(strFirst, strSecond))
            lstCompleteNewLines.append("{0} \\dotfill  & {1} \\\\\n".format(strFirst, strSecond))

        
        # make LaTeX main file
        mylines.reverse()
        arrAllLines = getSlic3rSummary(mylines)
        makeLaTeXMain(lstCompleteNewLines, arrAllLines)

        LaTexTemplate()
        LaTexStyle()


    except OSError as err:
        print("OS error: {0}".format(err))
    except:
        print('Somme silly error has occured: ' + str(sys.exc_info()[0]))
        out.write('Somme silly error has occured: ' + str(sys.exc_info()[0]))
        summ.close()
        out.close()
        bedshp.close()
        tplout.close()
        styout.close()
    else:
        summ.close()
        out.close()
        bedshp.close()
        tplout.close()
        styout.close()


def processGCodeLines(strLine, lowline, lstCompleteNewLines):
    if lowline.startswith('bed_shape'):
        strXYs = processBedShape(lowline)

        if bbed_shape:
            addtext = ''
            if bbed_shapetxt == False:
                addtext = 'Bed Shape & \\\\\n'

            # make a graphical representation of the bed shape - if desired
            bedgraph = addtext +' & \\begin{scaletikzpicturetowidth}{\\linewidth}\\begin{tikzpicture}[scale=\\tikzscale]\\path[line width=0.5mm, draw=black, fill=colbedshape] plot file {'+ str(outputbedshape.name) +'};\\draw[step=10, color=gray] ('+ str(gridxmin) +', '+ str(gridymin) +') grid ('+ str(gridxmax) +', '+ str(gridymax) +');\\end{tikzpicture}\\end{scaletikzpicturetowidth} \\\\\n'
            lstCompleteNewLines.append(bedgraph)

        if bbed_shapetxt:
            lstCompleteNewLines.append(strXYs)                    

    else:
            
        # remove tabs and replace with space
        strLine = strLine.replace('\t',' ')

        # make a list, so it can be reversed before reversing - wow! Yeah! I know!
        lstSublines = list()

        # split line by the equal sign
        sublines = strLine.split('=')[1].split('\\n')
                
        tmpsubl = processPostProcessLines(lowline,sublines[0])
        lstSublines.append("{0}: & \\\\\n".format(strLine.split('=')[0].title().replace('_',' ')))

        if len(sublines) > 0:
            for subline in sublines:
                subline = processPostProcessLines(lowline, subline)
                
                if ';' in subline:
                    strSecSplits = subline.split('; ')
                    subline = strSecSplits[0] + ' ; {\\color{CommentColor} ' + strSecSplits[1] + ' }'
                       
                lstSublines.append('\\multicolumn{2}{p{\\linewidth}}{\\bfseries\\ttfamily '+ subline +'} \\\\\n')
                            
        # reverse it (-1)
        lstSublines.reverse()
        lstCompleteNewLines.extend(lstSublines)


def processBedShape(bsline):

    global gridxmin
    global gridxmax
    global gridymin
    global gridymax

    bsline = rn(bsline)
    values = bsline.split('=')[1].split(',')
    xy = list()

    for value in values:
        val = value.split('x')

        x = float(val[0].strip())
        y = float(val[1].strip())

        # 0.05 is almost zero. 0.000005 is more than close enough to be zero.
        if x< .1 and x >- .1: x = 0
        if y< .1 and y >- .1: y = 0

        # check for min and max
        if x < gridxmin: gridxmin = x
        if y < gridymin: gridymin = y
        if x > gridxmax: gridxmax = x
        if y > gridymax: gridymax = y        

        bedshp.write(str(x) + ' ' + str(y) + '\n')
        xy.append('\\mbox{\\num{' + str(x) + '}$\\times$\\num{' + str(y) + '}}, ')
    
    # remove the last ,  and replace it with a .
    if xy[-1].endswith(', '):
        xy[-1] = xy[-1][:-2] + '.'
        
    strFirstLine = "{0} &   \\\\\n".format('Bed Shape')
    
    myxystr = ''
    for allxy in xy:
        myxystr = myxystr + ' ' + allxy 

    myxystr = '\\multicolumn{2}{p{\\linewidth}}{\\bfseries '+ myxystr +'} \\\\\n '

    return strFirstLine+myxystr


# make LaTeX main file
def makeLaTeXMain(lstCompleteNewLines, lstSummary):

    keepline = False
    strKeeper = ''
    lstKeepers = list()
    c = 0
    i = 0
    cf = 0

    # START of LaTeX file
    for sumline in lstSummary:
        lowline = sumline.lower()
        c = c + 1
        i = i + 1

        # messy but it works - so don't hit me, please.
        if 'generated' in lowline :
            sumline = sumline.replace(':','.')
            lstKeepers.append('Generated by: & ' + sumline.split('by')[1] + ' \\\\\n')
        elif 'part index' in lowline or 'filament usage' in lowline:
            lstKeepers.append('\n')
            lstKeepers.append('\\multicolumn{2}{l}{\\rule{0pt}{4ex}\\textbf{' + sumline + '}}\\\\\n')
            if lowline.startswith('filament usage'):cf += 1
        elif len(lowline) == 0 :
            keepline = False
            strKeeper = ''
        elif ':' in lowline and keepline == False:
            keepline = True
            strKeeper = sumline
            c = 0
        elif keepline == True:
            if c == 1:
                lstKeepers.append( strKeeper + ' & ' + sumline + ' \\\\\n')
            else:
                lstKeepers.append(  ' & ' + sumline + ' \\\\\n')
        elif 'width =' in lowline:
            lstKeepers.append(processSubSummaryline(sumline))
        elif cf >= 1:
            if cf >= 1:
                fili = processFilamentLine(sumline)
                lstKeepers.append(fili)                
            cf += 1
            if cf > 5: cf = 0
            
    for lnkeeper in lstKeepers:
        summ.write(LaTeXStringFilter(lnkeeper))

    summ.write('\\endinput\n\n')

    # un-reverse it (1) and write output to file
    lstCompleteNewLines.reverse()
    for newline in lstCompleteNewLines:
        out.write(newline)

    out.write('\\endinput\n\n')


def processFilamentLine(fline):

    fline = rn(fline)

    # find numbers with text (ie: 0.4mm)
    rgxnum = r"(\d+(?:\.\d*)?)"
    matchNum = 0
    strUnit = ''

    if '=' in fline:
        str1 = fline.split('=')[0]
        str2 = ''

        iFound = len(re.findall(rgxnum, fline.split('=')[1]))
       
        for m in re.finditer(rgxnum, fline.split('=')[1]):
            matchNum = matchNum + 1

            if 'cost' in fline:
                num = fline.split('=')[1].strip()
                str2 = '\\num{'+ num +'}'
                continue
             
            if 'used' in fline:
                if iFound == 1:
                    if matchNum == 1:
                        str2 = '\\SI{'+m.group()+'}{\\gram}'
                    else:
                        str2 = '\\SI{'+m.group()+'}{\\mm}'
                if iFound == 3:
                    if matchNum == 3: continue
                    if matchNum == 1:
                        str2 = '\\SI{'+m.group()+'}{\\mm}'
                    else:
                        str2 = str2 + ' \\SI{'+m.group()+'}{\\cubic\\cm}'

        fline = str1.title() +' \\dotfill & ' + str2 + ' \\\\\n'
    else:
        fline = fline +' & \\\\\n'

    return fline


def processSubSummaryline(sline):

    # find numbers with text (ie: 0.4mm)
    rgxnum = r"(\d+(?:\.\d*)?)"
    matchNum = 0

    if '=' in sline:
        str1 = sline.split('=')[0]
        str2 = ''

        for m in re.finditer(rgxnum, sline.split('=')[1]):
            matchNum = matchNum + 1
            if matchNum == 3:
                continue
            if matchNum == 1:
                str2 = '\\SI{' + m.group() + '}{\\mm}'
            if matchNum == 2:
                str2 = str2 + ' $\\approx$ \\SI[per-mode=fraction]{'+m.group()+'}{\\cubic\\mm\\per\\second}'

        sline = str1.title() +' \\dotfill & ' + str2 + ' \\\\\n'

    return sline



# Process PostProcessors
def processPostProcessLines(mylowline, mysubline):
    rgx = r"\"(.*)\"" # r"\"(.+?)\""
    if mylowline.startswith('post_process'):
        matches = re.findall(rgx,mysubline)             
        if matches: # there has to be a better way, yes?
            str = matches[0].replace('\\','/').replace('\\','/').replace('\\','/')
            str = str.replace('//','/').replace('//','/')
            mysubline = '{\\setlength{\\fboxsep}{4pt}\\setlength{\\fboxrule}{0pt}\\fbox{\\parbox{\\dimexpr\\linewidth-2\\fboxsep-2\\fboxrule\\relax}{\\directory[/]{'+str+'}}}}'

    # always do this:
    mysubline = LaTeXStringFilter(mysubline.replace(';', '; ').replace(',', ', '))
     
    return mysubline

       
def getSlic3rSummary(arrAllLines):
    lstNewLines = list()
    cnt = 0

    for line in arrAllLines:
        if line.startswith('M107'): # I only hope that this is always the case! Otherwise, how am I to find the end of the header?!
            break
        if '\n' in line:
            line = rn(line)
        if line.startswith(';') or not line.strip():
            line = line.replace('; ','')

            if line.lower().startswith('external perimeters extrusion width'):
                addendum = 'Part Index {0}'.format(cnt)
                lstNewLines.append(addendum)
                cnt += 1

            lstNewLines.append(line)
            #print(line)

    l=0
    arrAllLines.reverse()
    for filalins in arrAllLines:
        filalins = filalins.replace('; ','')
        if filalins.lower().startswith('total filament cost'):
            lstNewLines.append('Filament Usage')
            l = 1
        if l >= 1:
            lstNewLines.append(filalins)
            #print(filalins)
        
            if l >= 1: l += 1
        if l > 4: break

    return lstNewLines



def LaTexStyle():
    try:
        styout.write('\\NeedsTeXFormat{LaTeX2e}\n')
        styout.write('\\ProvidesPackage{'+ str(outputstyle.stem) +'}[2018/8/17 v1.0 '+ str(outputstyle.stem) +']\n')
        styout.write('\\RequirePackage[utf8]{inputenc}\n')
        styout.write('\\RequirePackage[T1]{fontenc}\n')
        styout.write('\\RequirePackage{lmodern}\n')
        styout.write('\\RequirePackage[includeheadfoot, includehead,heightrounded, left=3cm, right=2cm, top=1.5cm, bottom=1.5cm, footskip=1.7cm]{geometry}\n')
        styout.write('\\RequirePackage{booktabs}\n')
        styout.write('\\RequirePackage{ltablex}\n')
        styout.write('\\RequirePackage{siunitx}\n')
        styout.write('\\sisetup{detect-weight=true, detect-family=true, round-mode=places, round-precision=1}\n')
        styout.write('\\RequirePackage{menukeys}\n')
        styout.write('\\renewmenumacro{\\directory}[/]{pathswithblackfolder}\n')
        styout.write('\\RequirePackage[justification=justified, singlelinecheck=false, labelfont=bf]{caption}\n')
        styout.write('\\setlength\\parindent{0pt}\n')
        styout.write('\\RequirePackage{marginnote}\n')
        styout.write('\\reversemarginpar\n')
        styout.write('\\renewcommand*{\\marginfont}{\\footnotesize}\n')
        styout.write('\\renewcommand*{\\marginnotevadjust}{2pt}\n')
        styout.write('\\definecolor{color1}{RGB}{0,0,90}\n')
        styout.write('\\definecolor{color2}{RGB}{0,20,20}\n')
        if bbed_shape: styout.write('\\definecolor{colbedshape}{RGB}{247,240,221}\n')
        styout.write('\\usepackage[automark, footsepline, plainfootsepline, headsepline, plainheadsepline]{scrlayer-scrpage}\n')
        styout.write('\\pagestyle{scrheadings}\n')
        styout.write('\\ihead{\\huge \\bfseries{Slic3r Report}}\n')
        styout.write('\\rohead[\\filename{}]{\\filename{}}\n')
        styout.write('\\lofoot[Slic3r Configuration]{Slic3r Configuration}\n')
        styout.write('\\rofoot[\\author, \\date]{\\author, \\date}\n')
        styout.write('\\cohead{}\n')
        styout.write('\\setkomafont{pageheadfoot}{\\small}\n')
        styout.write('\\renewcommand\\tableofcontents{\\vspace{-14pt}\\@starttoc{toc}}\n')
        styout.write('\\newlength{\\tocsep}\n')
        styout.write('\\setlength\\tocsep{1.5pc} % Sets the indentation of the sections in the table of contents\n')
        styout.write('\\setcounter{tocdepth}{3} % Three levels in the table of contents section: sections, subsections and subsubsections\n')
        styout.write('\\RequirePackage{titletoc}\n')
        styout.write('\\contentsmargin{0cm}\n')
        styout.write('\\titlecontents{section}[\\tocsep]{\\addvspace{0pt}\\normalsize\\bfseries}{\\contentslabel[\\thecontentslabel]{\\tocsep}}{}{\\dotfill\\thecontentspage}[]\n')
        styout.write('\\titlecontents{subsection}[2\\tocsep]{\\addvspace{0pt}\\small}{\\contentslabel[\\thecontentslabel]{\\tocsep}}{}{\\ \\titlerule*[.5pc]{.}\\ \\thecontentspage}[]\n')
        styout.write('\\titlecontents*{subsubsection}[\\tocsep]{\\footnotesize}{}{}{}[\\ \\textbullet\\ ]\n')
        styout.write('\\definecolor{CommentColor}{HTML}{' + strFontCommentColor + '}')
        styout.write('\\endinput\n')
    except:
        styout.close()


def LaTexTemplate():
    try:

        tplout.write('\documentclass[ %\n')
        tplout.write('hyperref,\n')
        tplout.write('10pt,\n')
        tplout.write(']{scrartcl}\n')
        tplout.write('\\def\\filename{' + LaTeXStringFilter(str(filename.stem).title()) + '}\n')
        tplout.write('\\def\\author{'+ LaTeXStringFilter(strAuthor).title() +'}\n')
        tplout.write('\\def\\date{\\today}\n')
        tplout.write('\\usepackage{'+ str(outputstyle.stem) +'}\n')

        if bbed_shape: 
            tplout.write('\\usepackage{environ}\n')
            tplout.write('\\makeatletter\n')
            tplout.write('\\newsavebox{\\measure@tikzpicture}\n')
            tplout.write('\\NewEnviron{scaletikzpicturetowidth}[1]{\\def\\tikz@width{#1} \\def\\tikzscale{1}\\begin{lrbox}{\\measure@tikzpicture} \\BODY \\end{lrbox} \\pgfmathparse{#1/\\wd\\measure@tikzpicture} \\edef\\tikzscale{\\pgfmathresult} \\BODY}\n')
            tplout.write('\makeatother\n')

        tplout.write('\\usepackage{hyperref}\n')
        tplout.write('\\hypersetup{hidelinks, colorlinks=true, urlcolor=color2, citecolor=color1, linkcolor=color1, pdfauthor={\\author}, pdftitle={\\filename}, pdfsubject = {Slic3r Configuration Report: \\filename.gcode}, pdfcreator={LaTeX with a bunch of packages}, pdfproducer={pdflatex with a dash of Python}}\n')
        tplout.write('\\begin{document}\n')
        tplout.write('\\marginnote{Author:} 	{\\author} \\\\[5pt]\n')
        tplout.write('\\marginnote{Date:} 	    {\\date} \\\\[5pt]\n')

        tplout.write('\\marginnote{File:}  {\\textbf{\\filename} \\newline {\\setlength{\\fboxsep}{4pt}\\setlength{\\fboxrule}{0pt} \\fbox{\\parbox{\\dimexpr\\linewidth-2\\fboxsep-2\\fboxrule\\relax}{\\directory[/]{' + LaTeXStringFilter(str(filename.as_posix())) + '}}}}}\\\\[-2pt] \\rule{\\linewidth}{.4pt} \\\\[5pt]\n')

        # instead \\directory[/] use \\nolinkurl
        tplout.write('\\marginnote{Content:}    {\\tableofcontents}\n')
        tplout.write('\\vspace{-8pt}\\rule{\\linewidth}{.4pt}\n')
    
        if (bSection_Config == False):
            tplout.write('\\section{Summary}\n')
            tplout.write('\\begin{tabularx}{\\linewidth}{@{}p{7.5cm}>{\\bfseries}X@{}}\n')
            tplout.write('	\\caption{\\filename{} Summary} \\\\[-8pt] &  \\\\ \\toprule\n')
            tplout.write('	\\textbf{Option} & \\textbf{Value} \\\\ \\midrule\n')
            tplout.write('	\endhead	\n')
            tplout.write('		\\input{'+ str(outputsummary.stem) +'.tex}\n')
            tplout.write('	\\bottomrule\n')
            tplout.write('\\end{tabularx}\n')
            tplout.write('\\newpage\n')

        if (bSection_Summary == False):
            tplout.write('\\section{Slic3r Configuration}\n')
            tplout.write('\\begin{tabularx}{\\linewidth}{@{}p{7.5cm}>{\\bfseries}X@{}}\n')
            tplout.write('	\\caption{\\filename{} Slic3r-Configuration} \\\\[-8pt] &  \\\\ \\toprule\n')
            tplout.write('	\\textbf{Option} & \\textbf{Value} \\\\ \\midrule\n')
            tplout.write('	\\endhead	\n')
            tplout.write('		\\input{'+ str(outputconfig.stem) +'.tex}\n')
            tplout.write('	\\bottomrule\n')
            tplout.write('\\end{tabularx}\n')

        tplout.write('\\end{document}\n')
    except:
        tplout.close()


def rn(str):
    str = str.replace('\r','')
    str = str.replace('\n','')
    return str


def LaTeXStringFilter(mystring):
    mystring = mystring.replace('_','\_')

    return mystring


def runLaTeX():
    scriptdir = os.path.dirname(__file__)
    scriptdir_path = Path(scriptdir).resolve()
    runbatch = str(Path(str(scriptdir_path/'makepdf.bat')))
    texfile = str(Path(tplout.name).resolve())
    dir_path2 = str(dir_path)

    cmd = [ 'pdflatex', '-output-directory', dir_path2, '-interaction=nonstopmode', texfile] 

    for x in range(0, 2):
        proc = subprocess.Popen(cmd)
        proc.communicate()
    
    retcode = proc.returncode
    if not retcode == 0:
        os.unlink(dir_path/(pdfname+'.pdf'))
    else:
        if bOpenPDF:
            strpdf = str(Path(str(dir_path/(pdfname+'.pdf'))))
            subprocess.Popen(strpdf, shell = True)

    # TeX cleanup
    os.unlink(dir_path/(pdfname+'.toc'))
    os.unlink(dir_path/(pdfname+'.aux'))
    os.unlink(dir_path/(pdfname+'.log'))
    os.unlink(dir_path/(pdfname+'.out'))
    os.unlink(outputbedshape)
    os.unlink(outputsummary)
    os.unlink(outputconfig)
    os.unlink(outputstyle)
    os.unlink(outputtplout)


try:

    main()
    runLaTeX()
except:
    print('Somme silly snake-error has occured: ' + str(sys.exc_info()[0]))

