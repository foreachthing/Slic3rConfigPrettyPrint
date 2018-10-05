"""Creates a Package to be used in TeX and a CWL file for TeXstudio."""
#!/usr/bin/python

#TODO: Filament usage in Meter

import os
# from os import path
import sys
# import pathlib
from pathlib import Path, PureWindowsPath, PurePosixPath
import re  #regex
import argparse
import subprocess


# Users' Name - hopefully! (Thanks to 7eggert on github)
# If nothing was found, use 'Add Your Name' to let the user know it can be changed.
for name in ('USERNAME', 'LOGNAME', 'LNAME', 'USER'):
    currentusername = os.environ.get(name)
    if currentusername:
        break
    else:
        currentusername = 'Add Your Name'

## ArgumentParser
PARSER = argparse.ArgumentParser(
    prog=os.path.basename(__file__),
    description='Change the option prefix characters',
    prefix_chars='-+/',
    epilog='')

PARSER.add_argument('filename', nargs='?', help='Filename (GCode-File) to process.')
PARSER.add_argument('-au', '--author', metavar='"Author Name"', \
    default=currentusername, help='The Author of the GCode-File (default: %(default)s)')
#
GRP_DISABLE = PARSER.add_argument_group('Disable printing of ...', \
    'Note: -b and -t can be combined as -bt or -tb.')
GRP_DISABLE.add_argument('-b', action='store_false', \
    default=True, help='Bed Shape as graphic')
GRP_DISABLE.add_argument('-t', action='store_false', \
    default=True, help='Bed Shape as text (xy coordinates)')
GRP_DISABLE.add_argument('-g', action='store_false', \
    default=True, help='Removes all GCode fields (start, end, filament, layer, etc.)')
#
GRP_EXCLUSIV = PARSER.add_mutually_exclusive_group()
GRP_EXCLUSIV.add_argument('-c', action='store_true', \
    default=False, help='Print configuration section only')
GRP_EXCLUSIV.add_argument('-s', action='store_true', \
    default=False, help='Print summary section only')
#
PARSER.add_argument('-cc', '--commentcolor', action='store', type=str, metavar='hex', \
    default='FF0000', help='Font color of comments in HEX (default: %(default)s without leading #)')
PARSER.add_argument('-o', action='store_true', default=False, \
    help='Open PDF after creation (does not work in Linux).')

if len(sys.argv) <= 1:
    print('\n\n*** WARNING ***\nNo Parameter(s) provided but at least one \
        (GCode-filename) required. \n*** Type "[PROG_NAME] -h" for help ***\nI shall exit here.')
    exit(1)
try:
    ARGS = PARSER.parse_args()
except IOError as msg:
    PARSER.error(str(msg))

AUTHOR_NAME = ARGS.author
BED_SHAPE = ARGS.b
SECTION_CONFIG = ARGS.c
GCODE_FIELDS = ARGS.g
OPEN_PDF = ARGS.o
SECTION_SUMMARY = ARGS.s
BED_SHAPETEXT = ARGS.t
FILENAME = ARGS.filename
FONT_COMMENT_COLOR = ARGS.commentcolor.upper() # Needs to be upper-case
## END ArgumentParser

# Absolute path of gcode-file
ABSOLUTE_PATH = os.path.abspath(FILENAME)

if os.name == 'nt':
    ## get and set paths
    DIR_PATH = Path(ABSOLUTE_PATH).parents[0]
    PDF_NAME = Path(FILENAME).stem
    # define output files
    TEXOUT_FILE = open(DIR_PATH/'slic3rconfigtable.tex', 'w')
    OUTPUTCONFIG = PureWindowsPath(str(TEXOUT_FILE.name))
     # Summary
    SUMMARY_FILE = open(DIR_PATH/'slic3rsummary.tex', 'w')
    OUTPUTSUMMARY = PureWindowsPath(str(SUMMARY_FILE.name))
     # Bedshape
    BEDSHAPE_FILE = open(DIR_PATH/'slic3rbedshape.data', 'w')
    OUTPUTBEDSHAPE = PureWindowsPath(str(BEDSHAPE_FILE.name))
     # Main TEX file
    TPLOUT_FILE = open(DIR_PATH/(PDF_NAME+'.tex'), 'w')
    OUTPUTTPLOUT = PureWindowsPath(str(TPLOUT_FILE.name))
     # Main Style file
    STYOUT_FILE = open(DIR_PATH/'GCodeSuperStylin.sty', 'w')
    OUTPUTSTYLE = PureWindowsPath(str(STYOUT_FILE.name))

else:
    ## get and set paths
    DIR_PATH = PurePosixPath(ABSOLUTE_PATH).parent
    PDF_NAME = Path(FILENAME).stem
    # define output files
    TEXOUT_FILE = open(str(DIR_PATH/'slic3rconfigtable.tex'), 'w')
    OUTPUTCONFIG = Path(str(TEXOUT_FILE.name))
     # Summary
    SUMMARY_FILE = open(str(DIR_PATH/'slic3rsummary.tex'), 'w')
    OUTPUTSUMMARY = Path(str(SUMMARY_FILE.name))
     # Bedshape
    BEDSHAPE_FILE = open(str(DIR_PATH/'slic3rbedshape.data'), 'w')
    OUTPUTBEDSHAPE = Path(str(BEDSHAPE_FILE.name))
     # Main TEX file
    TPLOUT_FILE = open(str(DIR_PATH/(PDF_NAME+'.tex')), 'w')
    OUTPUTTPLOUT = Path(str(TPLOUT_FILE.name))
     # Main Style file
    STYOUT_FILE = open(str(DIR_PATH/'GCodeSuperStylin.sty'), 'w')
    OUTPUTSTYLE = Path(str(STYOUT_FILE.name))

# global vars for grid in bed shape
GRIDXMIN = float(0)
GRIDXMAX = float(0)
GRIDYMIN = float(0)
GRIDYMAX = float(0)

def main():
    """Main Process"""
    # if no file specified, exit! If it comes to that ...
    if str(FILENAME).lower() == 'none':
        print('No Parameter for "filename" provided. I shall exit here.')
        exit(1)

    gcode_file = open(FILENAME, 'r')
    gcode_lines = gcode_file.readlines()
    gcode_file.close()

    # main list
    list_completenewlines = list()

    try:
        # first_line = gcode_lines[0] # Slic3r Info

        # reverse it and stop at the first empty line
        gcode_lines.reverse()
        # i = 0

        for str_line in gcode_lines:

            if str_line.startswith('\n') or str_line.strip() == '':
                break
            if '\n' in str_line:
                str_line = rn_replace(str_line)
            if '\\n' in str_line and not str_line.endswith('\n'):
                str_line = str_line.replace('\\n', ' \\n ')

            str_line = str_line.replace('; ', '', 1) # replace only first occurence

            ## Some more replacements for LaTeX
            str_line = str_line.replace('%', '\\%')
            str_line = str_line.replace('#', '\\#')
            str_line = str_line.replace('[', '{[')
            str_line = str_line.replace(']', ']}')
            lowline = str_line.lower()

            if (lowline.startswith('start_gcode') or lowline.startswith('end_gcode')
                    or lowline.startswith('between_objects_gcode')
                    or lowline.startswith('layer_gcode')
                    or lowline.startswith('before_layer_gcode')
                    or lowline.startswith('post_process')
                    or lowline.startswith('bed_shape')
                    or lowline.startswith('notes')
                    or lowline.startswith('printer_notes')
                    or lowline.startswith('filament_notes')
                    or lowline.startswith('end_filament_gcode')
                    or lowline.startswith('start_filament_gcode')):
                if GCODE_FIELDS is False:
                    if (lowline.startswith('start_gcode')
                            or lowline.startswith('end_gcode')
                            or lowline.startswith('between_objects_gcode')
                            or lowline.startswith('layer_gcode')
                            or lowline.startswith('before_layer_gcode')):
                        #print('no gcode please')
                        continue
                    else:
                        processgcodelines(str_line, lowline, list_completenewlines)
                        continue

                else:
                    processgcodelines(str_line, lowline, list_completenewlines)
                    continue

            spline = str_line.split('=')

            str_first = spline[0].title().replace('_', ' ')
            str_second = latexstringfilter(spline[1])

            list_completenewlines.append('{0} \\dotfill  \
                & {1} \\\\\n'.format(str_first, str_second))

        # make LaTeX files
        gcode_lines.reverse()
        arr_alllines = getslic3rsummary(gcode_lines)
        makelatexsummary(list_completenewlines, arr_alllines)

        latextemplate()
        latexstyle()

    except OSError as err:
        print('OS error: {0} in {1}'.format(err, err.filename))
    except Exception as ex:
        print(str(ex))
        TEXOUT_FILE.write(str(ex))

        SUMMARY_FILE.close()
        TEXOUT_FILE.close()
        BEDSHAPE_FILE.close()
        TPLOUT_FILE.close()
        STYOUT_FILE.close()
    else:
        SUMMARY_FILE.close()
        TEXOUT_FILE.close()
        BEDSHAPE_FILE.close()
        TPLOUT_FILE.close()
        STYOUT_FILE.close()


def processgcodelines(str_line, lowline, list_completenewlines):
    """Process all GCode lines"""
    if lowline.startswith('bed_shape'):
        strxys = processbedshape(lowline)

        if BED_SHAPE:
            addtext = ''
            if BED_SHAPETEXT is False:
                addtext = 'Bed Shape & \\\\\n'

            # make a graphical representation of the bed shape
            bedgraph = addtext +' & \\begin{scaletikzpicturetowidth}{\\linewidth}\
                \\begin{tikzpicture}[scale=\\tikzscale]\
                \\path[line width=0.5mm, draw=black, fill=colbedshape] \
                plot file {'+ str(OUTPUTBEDSHAPE.name) +'};\
                \\draw[step=10, color=gray] ('+ str(GRIDXMIN) +',\
                '+ str(GRIDYMIN) +') grid ('+ str(GRIDXMAX) +', '+ str(GRIDYMAX)\
                +');\\end{tikzpicture}\\end{scaletikzpicturetowidth} \\\\\n'
            list_completenewlines.append(bedgraph)

        if BED_SHAPETEXT:
            list_completenewlines.append(strxys)

    else:

        # remove tabs and replace with space
        str_line = str_line.replace('\t', ' ')

        # make a list, so it can be reversed before reversing - wow! Yeah! I know!
        lstsublines = list()

        # split line by the equal sign
        sublines = str_line.split('=')[1].split('\\n')

        # tmpsubl = processpostprocesslines(lowline, sublines[0])
        lstsublines.append('{0}: & \\\\\n'.format(str_line.split('=')[0].title().replace('_', ' ')))

        if sublines:
            for subline in sublines:
                subline = processpostprocesslines(lowline, subline)

                if ';' in subline:
                    strsecsplits = subline.split('; ')
                    subline = strsecsplits[0] + ' ; \
                        {\\color{CommentColor} ' + strsecsplits[1] + ' }'

                lstsublines.append('\\multicolumn{2}{p{\
                    \\linewidth}}{\\bfseries\\ttfamily '+ subline +'} \\\\\n')

        # reverse it (-1)
        lstsublines.reverse()
        list_completenewlines.extend(lstsublines)


def processbedshape(bsline):
    """Process the Bed Shape and prepare everything to be printed as graphics"""
    global GRIDXMIN
    global GRIDXMAX
    global GRIDYMIN
    global GRIDYMAX

    bsline = rn_replace(bsline)
    values = bsline.split('=')[1].split(',')
    xy_list = list()

    for value in values:
        val = value.split('x')

        x_coord = float(val[0].strip())
        y_coord = float(val[1].strip())

        # +-0.1 is close enough to be zero.
        if   0.1 > x_coord < -0.1:
            x_coord = 0
        if  0.1 > y_coord < -0.1:
            y_coord = 0

        # check for min and max
        if x_coord < GRIDXMIN:
            GRIDXMIN = x_coord
        if y_coord < GRIDYMIN:
            GRIDYMIN = y_coord
        if x_coord > GRIDXMAX:
            GRIDXMAX = x_coord
        if y_coord > GRIDYMAX:
            GRIDYMAX = y_coord

        BEDSHAPE_FILE.write(str(x_coord) + ' ' + str(y_coord) + '\n')
        xy_list.append('\\mbox{\\num{' + str(x_coord) + '}$\\times$\\num{' + str(y_coord) + '}}, ')

    # remove the last ,  and replace it with a .
    if xy_list[-1].endswith(', '):
        xy_list[-1] = xy_list[-1][:-2] + '.'

    first_line = '{0} &   \\\\\n'.format('Bed Shape')

    myxystr = ''
    for allxy in xy_list:
        myxystr = myxystr + ' ' + allxy

    myxystr = '\\multicolumn{2}{p{\\linewidth}}{\\bfseries '+ myxystr +'} \\\\\n '

    return first_line+myxystr


# make LaTeX main file
def makelatexsummary(list_completenewlines, lstsummary):
    """Print GCODE-Summary"""
    keepline = False
    strkeeper = ''
    list_keepers = list()
    c_count = 0
    cf_count = 0

    # START of LaTeX file
    for sumline in lstsummary:
        lowline = sumline.lower()
        c_count = c_count + 1

        # messy but it works - so don't hit me, please.
        if 'generated' in lowline:
            sumline = sumline.replace(':', '.')
            list_keepers.append('Generated by: & ' + sumline.split('by')[1] + ' \\\\\n')
        elif 'part index' in lowline or 'filament usage' in lowline:
            list_keepers.append('\n')
            list_keepers.append('\\multicolumn{2}{l}{\
                \\rule{0pt}{4ex}\\textbf{' + sumline + '}}\\\\\n')
            if lowline.startswith('filament usage'):
                cf_count += 1
        elif not lowline:
            keepline = False
            strkeeper = ''
        elif ':' in lowline and keepline is False:
            keepline = True
            strkeeper = sumline
            c_count = 0
        elif keepline is True:
            if c_count == 1:
                list_keepers.append(strkeeper + ' & ' + sumline + ' \\\\\n')
            else:
                list_keepers.append(' & ' + sumline + ' \\\\\n')
        elif 'width =' in lowline:
            list_keepers.append(processsubsummaryline(sumline))
        elif cf_count >= 1:
            if cf_count >= 1:
                fili = processfilamentline(sumline)
                list_keepers.append(fili)
            cf_count += 1
            if cf_count > 5:
                cf_count = 0

    for lnkeeper in list_keepers:
        SUMMARY_FILE.write(latexstringfilter(lnkeeper))

    SUMMARY_FILE.write('\\endinput\n\n')

    # un-reverse it (1) and write output to file
    list_completenewlines.reverse()
    for newline in list_completenewlines:
        TEXOUT_FILE.write(newline)

    TEXOUT_FILE.write('\\endinput\n\n')


def processfilamentline(fline):
    """Process Filament info"""
    fline = rn_replace(fline)

    # find numbers with text (ie: 0.4mm)
    rgxnum = r"(\d+(?:\.\d*)?)"
    matchnum = 0

    if '=' in fline:
        str1 = fline.split('=')[0]
        str2 = ''

        ifound = len(re.findall(rgxnum, fline.split('=')[1]))

        for lvalue in re.finditer(rgxnum, fline.split('=')[1]):
            matchnum = matchnum + 1

            if 'cost' in fline:
                num = fline.split('=')[1].strip()
                str2 = '\\num{'+ num +'}'
                continue

            if 'used' in fline:
                if ifound == 1:
                    if matchnum == 1:
                        str2 = '\\SI{'+lvalue.group()+'}{\\gram}'
                    else:
                        str2 = '\\SI{'+lvalue.group()+'}{\\mm}'
                if ifound == 3:
                    if matchnum == 3:
                        continue
                    if matchnum == 1:
                        str2 = '\\SI{'+lvalue.group()+'}{\\mm}'
                    else:
                        str2 = str2 + ' \\SI{'+lvalue.group()+'}{\\cubic\\cm}'

        fline = str1.title() +' \\dotfill & ' + str2 + ' \\\\\n'
    else:
        fline = fline +' & \\\\\n'

    return fline


def processsubsummaryline(sline):
    """Process SUB-Summary Lines"""
    # find numbers with text (ie: 0.4mm)
    rgxnum = r"(\d+(?:\.\d*)?)"
    matchnum = 0

    if '=' in sline:
        str1 = sline.split('=')[0]
        str2 = ''

        for lvalue in re.finditer(rgxnum, sline.split('=')[1]):
            matchnum = matchnum + 1
            if matchnum == 3:
                continue
            if matchnum == 1:
                str2 = '\\SI{' + lvalue.group() + '}{\\mm}'
            if matchnum == 2:
                str2 = str2 + ' $\\approx$ \\SI[per-mode=fraction]\
                    {'+lvalue.group()+'}{\\cubic\\mm\\per\\second}'

        sline = str1.title() +' \\dotfill & ' + str2 + ' \\\\\n'

    return sline



# Process PostProcessors
def processpostprocesslines(mylowline, mysubline):
    """Make a list of all the Post Processors"""
    rgx = r"\"(.*)\""
    if mylowline.startswith('post_process'):
        matches = re.findall(rgx, mysubline)
        if matches: # there has to be a better way, yes?
            strng = matches[0].replace('\\', '/').replace('\\', '/').replace('\\', '/')
            strng = strng.replace('//', '/').replace('//', '/')
            mysubline = '{\\setlength{\\fboxsep}{4pt}\\setlength{\
                \\fboxrule}{0pt}\\fbox{\\parbox{\\dimexpr\
                \\linewidth-2\\fboxsep-2\\fboxrule\\relax}\
                {\\directory[/]{'+strng+'}}}}'

    # always do this:
    mysubline = latexstringfilter(mysubline.replace(';', '; ').replace(', ', ', '))

    return mysubline


def getslic3rsummary(arr_alllines):
    """Slic3r Summary"""
    list_newlines = list()
    cnt = 0

    for line in arr_alllines:
        # I only hope that this is always the case! Otherwise,
        # how am I to find the end of the header?!
        if line.startswith('M107'):
            break
        if '\n' in line:
            line = rn_replace(line)
        if line.startswith(';') or not line.strip():
            line = line.replace('; ', '')

            if line.lower().startswith('external perimeters extrusion width'):
                addendum = 'Part Index {0}'.format(cnt)
                list_newlines.append(addendum)
                cnt += 1

            list_newlines.append(line)
            #print(line)

    lcont = 0
    arr_alllines.reverse()
    for filalins in arr_alllines:
        filalins = filalins.replace('; ', '')
        if filalins.lower().startswith('total filament cost'):
            list_newlines.append('Filament Usage')
            lcont = 1
        if lcont >= 1:
            list_newlines.append(filalins)
            #print(filalins)

            if lcont >= 1:
                lcont += 1
        if lcont > 4:
            break

    return list_newlines


def latexstyle():
    """Writes the Package file content"""
    try:
        STYOUT_FILE.write('\\NeedsTeXFormat{LaTeX2e}\n')
        STYOUT_FILE.write('\\ProvidesPackage{'+ str(OUTPUTSTYLE.stem) +'}\
            [2018/8/17 v1.0 '+ str(OUTPUTSTYLE.stem) +']\n')
        STYOUT_FILE.write('\\RequirePackage[utf8]{inputenc}\n')
        STYOUT_FILE.write('\\RequirePackage[T1]{fontenc}\n')
        STYOUT_FILE.write('\\RequirePackage{lmodern}\n')
        STYOUT_FILE.write('\\RequirePackage[includeheadfoot, includehead, \
            heightrounded, left=3cm, right=2cm, top=1.5cm, \
            bottom=1.5cm, footskip=1.7cm]{geometry}\n')
        STYOUT_FILE.write('\\RequirePackage{booktabs}\n')
        STYOUT_FILE.write('\\RequirePackage{ltablex}\n')
        STYOUT_FILE.write('\\RequirePackage{siunitx}\n')
        STYOUT_FILE.write('\\sisetup{detect-weight=true, detect-family=true, \
            round-mode=places, round-precision=1}\n')
        STYOUT_FILE.write('\\RequirePackage{menukeys}\n')
        STYOUT_FILE.write('\\renewmenumacro{\\directory}[/]\
            {pathswithblackfolder}\n')
        STYOUT_FILE.write('\\RequirePackage[justification=justified, \
            singlelinecheck=false, labelfont=bf]{caption}\n')
        STYOUT_FILE.write('\\setlength\\parindent{0pt}\n')
        STYOUT_FILE.write('\\RequirePackage{marginnote}\n')
        STYOUT_FILE.write('\\reversemarginpar\n')
        STYOUT_FILE.write('\\renewcommand*{\\marginfont}{\\footnotesize}\n')
        STYOUT_FILE.write('\\renewcommand*{\\marginnotevadjust}{2pt}\n')
        STYOUT_FILE.write('\\definecolor{color1}{RGB}{0, 0, 90}\n')
        STYOUT_FILE.write('\\definecolor{color2}{RGB}{0, 20, 20}\n')
        STYOUT_FILE.write('\\definecolor{CommentColor}{HTML}{' + FONT_COMMENT_COLOR + '}\n')

        if BED_SHAPE:
            STYOUT_FILE.write('\\definecolor{colbedshape}{RGB}{247, 240, 221}\n')

        STYOUT_FILE.write('\\usepackage[automark, footsepline, plainfootsepline, \
            headsepline, plainheadsepline]{scrlayer-scrpage}\n')
        STYOUT_FILE.write('\\pagestyle{scrheadings}\n')
        STYOUT_FILE.write('\\ihead{\\huge \\bfseries{Slic3r Report}}\n')
        STYOUT_FILE.write('\\rohead[\\filename{}]{\\filename{}}\n')
        STYOUT_FILE.write('\\lofoot[Slic3r Configuration]{Slic3r Configuration}\n')
        STYOUT_FILE.write('\\rofoot[\\author, \\date]{\\author, \\date}\n')
        STYOUT_FILE.write('\\cohead{}\n')
        STYOUT_FILE.write('\\setkomafont{pageheadfoot}{\\small}\n')
        STYOUT_FILE.write('\\renewcommand\\tableofcontents{\\vspace{-14pt}\\@starttoc{toc}}\n')
        STYOUT_FILE.write('\\newlength{\\tocsep}\n')
        STYOUT_FILE.write('\\setlength\\tocsep{1.5pc}\n')
        STYOUT_FILE.write('\\setcounter{tocdepth}{3}\n')
        STYOUT_FILE.write('\\RequirePackage{titletoc}\n')
        STYOUT_FILE.write('\\contentsmargin{0cm}\n')
        STYOUT_FILE.write('\\titlecontents{section}[\\tocsep]{\\addvspace{0pt}\
            \\normalsize\\bfseries}{\\contentslabel[\\thecontentslabel]{\\tocsep}}\
            {}{\\dotfill\\thecontentspage}[]\n')
        STYOUT_FILE.write('\\titlecontents{subsection}[2\\tocsep]{\\addvspace{0pt}\\small}\
            {\\contentslabel[\\thecontentslabel]{\\tocsep}}\
            {}{\\ \\titlerule*[.5pc]{.}\\ \\thecontentspage}[]\n')
        STYOUT_FILE.write('\\titlecontents*{subsubsection}[\\tocsep]\
            {\\footnotesize}{}{}{}[\\ \\textbullet\\ ]\n')
        STYOUT_FILE.write('\n\\endinput\n')
    except Exception as ex:
        STYOUT_FILE.close()
        print(str(ex))


def latextemplate():
    """Writes the main TeX file. This "file" can be changed to match your style or layout"""
    try:

        TPLOUT_FILE.write('\\documentclass[ %\n')
        TPLOUT_FILE.write('hyperref, \n')
        TPLOUT_FILE.write('10pt, \n')
        TPLOUT_FILE.write(']{scrartcl}\n')
        TPLOUT_FILE.write('\\def\\filename{' + latexstringfilter(PDF_NAME) + '.gcode}\n')
        TPLOUT_FILE.write('\\def\\author{'+ latexstringfilter(AUTHOR_NAME) +'}\n')
        TPLOUT_FILE.write('\\def\\date{\\today}\n')
        TPLOUT_FILE.write('\\usepackage{'+ str(OUTPUTSTYLE.stem) +'}\n')

        if BED_SHAPE:
            TPLOUT_FILE.write('\\usepackage{environ}\n')
            TPLOUT_FILE.write('\\makeatletter\n')
            TPLOUT_FILE.write('\\newsavebox{\\measure@tikzpicture}\n')
            TPLOUT_FILE.write('\\NewEnviron{scaletikzpicturetowidth}[1]\
                {\\def\\tikz@width{#1} \\def\\tikzscale{1}\\begin{lrbox}\
                {\\measure@tikzpicture} \\BODY \\end{lrbox} \
                \\pgfmathparse{#1/\\wd\\measure@tikzpicture} \
                \\edef\\tikzscale{\\pgfmathresult} \\BODY}\n')
            TPLOUT_FILE.write('\\makeatother\n')

        TPLOUT_FILE.write('\\usepackage{hyperref}\n')
        TPLOUT_FILE.write('\\hypersetup{hidelinks, colorlinks=true, \
            urlcolor=color2, citecolor=color1, linkcolor=color1, \
            pdfauthor={\\author}, pdftitle={\\filename}, \
            pdfsubject = {Slic3r Configuration Report: \\filename.gcode}, \
            pdfcreator={LaTeX with a bunch of packages}, \
            pdfproducer={pdflatex with a dash of Python}}\n')
        TPLOUT_FILE.write('\\begin{document}\n')
        TPLOUT_FILE.write('\\marginnote{Author:} 	{\\author} \\\\[5pt]\n')
        TPLOUT_FILE.write('\\marginnote{Date:} 	    {\\date} \\\\[5pt]\n')

        newpath = latexstringfilter(str(ABSOLUTE_PATH.replace(os.path.sep, ';')))
        TPLOUT_FILE.write('\\marginnote{File:}  {\\textbf{\\filename} \
            \\newline {\\setlength{\\fboxsep}{4pt}\\setlength{\\fboxrule}{0pt} \
            \\fbox{\\parbox{\\dimexpr\\linewidth-2\\fboxsep-2\\fboxrule\\relax}\
            {\\directory[;]{' + newpath + '}}}}}\\\\[-2pt] \\rule{\\linewidth}{.4pt} \\\\[5pt]\n')

        TPLOUT_FILE.write('\\marginnote{Content:}    {\\tableofcontents}\n')
        TPLOUT_FILE.write('\\vspace{-8pt}\\rule{\\linewidth}{.4pt}\n')

        if SECTION_CONFIG is False:
            TPLOUT_FILE.write('\\section{Summary}\n')
            TPLOUT_FILE.write('\\begin{tabularx}{\\linewidth}{@{}p{7.5cm}>{\\bfseries}X@{}}\n')
            TPLOUT_FILE.write('	\\caption{\\filename{} Summary} \\\\[-8pt] &  \\\\ \\toprule\n')
            TPLOUT_FILE.write('	\\textbf{Option} & \\textbf{Value} \\\\ \\midrule\n')
            TPLOUT_FILE.write('	\\endhead	\n')
            TPLOUT_FILE.write('		\\input{'+ str(OUTPUTSUMMARY.stem) + '.tex}\n')
            TPLOUT_FILE.write('	\\bottomrule\n')
            TPLOUT_FILE.write('\\end{tabularx}\n')
            TPLOUT_FILE.write('\\newpage\n')

        if SECTION_SUMMARY is False:
            TPLOUT_FILE.write('\\section{Slic3r Configuration}\n')
            TPLOUT_FILE.write('\\begin{tabularx}{\\linewidth}{@{}p{7.5cm}>{\\bfseries}X@{}}\n')
            TPLOUT_FILE.write('	\\caption{\\filename{} Slic3r-Configuration} \\\\[-8pt] \
                &  \\\\ \\toprule\n')
            TPLOUT_FILE.write('	\\textbf{Option} & \\textbf{Value} \\\\ \\midrule\n')
            TPLOUT_FILE.write('	\\endhead\n')
            TPLOUT_FILE.write('		\\input{'+ str(OUTPUTCONFIG.stem) + '.tex}\n')
            TPLOUT_FILE.write('	\\bottomrule\n')
            TPLOUT_FILE.write('\\end{tabularx}\n')

        TPLOUT_FILE.write('\\end{document}\n')

    except Exception as ex:
        TPLOUT_FILE.close()
        print(str(ex))


def rn_replace(strreplace):
    """Remove all \r and \n"""
    strreplace = strreplace.replace('\r', '')
    strreplace = strreplace.replace('\n', '')
    return strreplace


def latexstringfilter(mystring):
    """Additional TeX-Filters. Revove stuff TeX does not like."""
    mystring = mystring.replace('_', '\_')

    return mystring


def runlatex():
    """Run TeX and remove all temp files"""
    # files to clean
    cleanup = list()
    cleanup = [OUTPUTBEDSHAPE, OUTPUTSUMMARY, OUTPUTCONFIG, OUTPUTSTYLE, OUTPUTTPLOUT]
    tocfile = Path(DIR_PATH/str(PDF_NAME + '.toc'))
    auxfile = Path(DIR_PATH/str(PDF_NAME + '.aux'))
    logfile = Path(DIR_PATH/str(PDF_NAME + '.log'))
    outfile = Path(DIR_PATH/str(PDF_NAME + '.out'))
    pdffile = Path(DIR_PATH/str(PDF_NAME + '.pdf'))

    if os.name == 'nt':
        # the joy of Windows
        texfile = PureWindowsPath(TPLOUT_FILE.name)
        pdffile = PureWindowsPath(str(pdffile))
        tocfile = PureWindowsPath(str(tocfile))
        auxfile = PureWindowsPath(str(auxfile))
        logfile = PureWindowsPath(str(logfile))
        outfile = PureWindowsPath(str(outfile))

    else:
        texfile = PurePosixPath(TPLOUT_FILE.name)

    # more files to clean up
    cleanup.append(tocfile)
    cleanup.append(auxfile)
    cleanup.append(logfile)
    cleanup.append(outfile)

    cmd = ['pdflatex', '-output-directory', str(DIR_PATH), '-interaction=nonstopmode', str(texfile)]

    # make two runs because of TOC
    for iruns in range(0, 2):
        proc = subprocess.Popen(cmd)
        proc.communicate()

    retcode = proc.returncode
    if retcode != 0:
        print('Error occured in .tex and PDF will be removed.')
        cleanup.append(pdffile)

    else:
        if OPEN_PDF is True:
            if os.name == 'nt':
                subprocess.Popen(str(pdffile), shell=True)
            else:
                # this wont work on my ubunut...?
                os.system('/usr/bin/xdg-open ' + str(pdffile))

    # TeX cleanup
    try:
        for file in cleanup:
            if os.path.exists(str(file)):
                print('Removing file: ' + str(file))
                os.remove(str(file))
    except OSError as exp:
        print('Error: {0} - {1}.'.format(exp.filename, exp.strerror))

    if os.path.exists(str(pdffile)):
        print('\n\nYour document is ready at {0}.'.format(str(pdffile)))


try:
    main()
    runlatex()

except Exception as ex:
    print(str(ex))
