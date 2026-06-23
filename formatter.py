# dependencies:
#  - BeautifulSoup (python)
#  - lxml (python)
#  - pandoc

import sys
import subprocess
from bs4 import BeautifulSoup

SKIP = ['\\begin{problemsonly}', '\\end{problemsonly}', '\\maketitle']
SKIP_ALL = ['\\begin{solution}', '\\begin{rubric}', '\\begin{hint}']
END_ALL = ['\\end{solution}', '\\end{rubric}', '\\end{hint}']

REPLACE = {'enumeratequestions': 'enumerate',
        '\\pred': '\\texttt',
        '\\imp': '\\rightarrow',
        '\\biimp': '\\leftrightarrow',
        "’": "'"
    }

STYLES = {".center h2": 'text-align: center; margin-top: 1em;',
        ".example": "border: 2px solid blue; border-radius: .75rem; background-color: rgba(0,0,255,0.05); padding: 0 .5rem;",
        "ol": "list-style-type: lower-alpha;",
        ".displayquote": "color: black;", 
        "dl": "display: grid; grid-gap: 4px 16px; grid-template-columns: max-content;",
        "dl dt": "font-weight: bold;",
        "dl dd": "margin: 0; grid-column-start: 2;",
        "dl dd p": "margin: 0;"
    }

# convert input latex file formatted using 151 class into readable input for pandoc
def clean_latex(input, output):
    with open(input) as fp:
        with open(output, 'w') as out:
            skip = False
            for line in fp:
                l = line.strip()
                
                if l in SKIP_ALL:
                    skip = True
                    continue
                elif l in END_ALL:
                    skip = False
                    continue
                elif l in SKIP or skip or l.startswith('\\vspace'):       
                    continue
                else:
                    l = line
                    for r, w in REPLACE.items():
                       l = l.replace(r, w)
                    if 'verb' in l:
                        l = l.replace("\\verb|", "\\texttt{")
                        l = l.replace("|", "}")
                    out.write(l)


def reformat(input, output):
    with open(input) as fp:
        soup = BeautifulSoup(fp, 'lxml')

        # fix subheadings
        h2s = soup.find_all('h2')
        for h in h2s:
            h.name = 'h3'
        
        # fix section headings
        sec_headers = soup.find_all(class_='center')
        for div in sec_headers:
            h = div.find('h1')
            if h:
                h.name = 'h2'
        
        # fix problem titles
        p_headers = soup.find_all('h1')
        for tag in p_headers:
            c = tag.get('class')
            if c == None:
                tag.name = 'h3'
            elif 'title' not in c:
                tag.name = 'h3'

        # fix display quotes
        quotes = soup.find_all(class_='displayquote')
        for q in quotes:
            q.name = 'blockquote'

        # strip annotation tags
        annotations = soup.find_all('annotation')
        for a in annotations:
            a.decompose()

        # apply styling
        for identifier, style in STYLES.items():
            apply_styles(identifier.split(), soup, style)



        # write output
        with open(output, "w") as file:
            file.write(str(soup.find('body')))

def apply_styles(search, tree, style):
    s = search[0]
    results = None
    if s.startswith("."):
        results = tree.find_all(class_=s[1:])
    elif s.startswith("#"):
        results = tree.find_all(id=s[1:])
    else: 
        results = tree.find_all(s)
    
    if results:
        for r in results:
            if len(search) == 1:
                r['style'] = style
            else:
                apply_styles(search[1:], r, style)

# run the file as py formatter.py [input/path] [output/path] [optional: metadata/path]
if __name__ == "__main__":
    if len(sys.argv) > 4 or len(sys.argv) < 3:
        print('incorrect number of arguments')
        print('run the file as `py formatter.py [input/path] [output/path] [optional: metadata/path]`')
        exit()

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    in_name = input_path.split(".")[0]
    out_name = output_path.split(".")[0]

    clean_input_path = f"{in_name}-clean.tex"
    clean_latex(input_path, clean_input_path)

    pre_out_path = f"{out_name}-pre.html"
    
    # no metadata
    if len(sys.argv) == 3:
        subprocess.run(["pandoc", clean_input_path, '-f', 'latex+auto_identifiers', '-t', 'html', '-s', '-o', pre_out_path, '--mathml', '--number-sections', '--template', 'pset.html5'])
    # metadata
    elif len(sys.argv) == 4:
        metadata_path = sys.argv[3]
        subprocess.run(["pandoc", clean_input_path, '-f', 'latex+auto_identifiers', '-t', 'html', '-s', '-o', pre_out_path, '--mathml', '--number-sections', '--template', 'pset.html5', '--metadata-file', metadata_path])

    reformat(pre_out_path, f'{out_name}.html')
    subprocess.run(["rm", "-rf", pre_out_path])
    subprocess.run(["rm", "-rf", clean_input_path])
