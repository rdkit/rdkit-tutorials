# Copyright (C) 2016 Greg Landrum
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
from __future__ import print_function
import os,warnings,sys
import nbformat

def _notebook_read(path):
    """Read a notebook using nbformat
    """
    inf = open(path)
    nb = nbformat.read(inf,nbformat.current_nbformat)
    return nb

def _handle_multilinetext(txt,quotes):
    keep_txt = []
    stxt = txt.split(quotes)
    for i in range(0,len(stxt),2):
        piece = stxt[i]
        if piece[0] == '\n':
            piece = piece[1:]
        if piece == '':
            continue
        keep_txt.extend(piece.split("\n"))
        if i+1<len(stxt): # still a text block here
            keep_txt[-1] = keep_txt[-1]+quotes+"\n... ".join(stxt[i+1].split("\n"))+quotes
    return keep_txt


import re

ptr_expr = re.compile(r'<(.*) at 0x.*>')
ignore_expr = re.compile(r'#\W*doctest:\W*IGNORE')
img_expr = re.compile(r'<img src=.*>')
def process_cell(cell):
    txt = cell['source']
    if ignore_expr.search(txt):
        return None,None
    if not txt:
        return None,None
    if txt[0]=='!' or txt.find('\n!')!=-1:
        warnings.warn("ipython shell command found in cell. Skipping the cell.")
        return None,None
    if txt[0]=='%' or txt.find('\n%')!=-1:
        warnings.warn("ipython magic command found in cell. Skipping the cell.")
        return None,None

    # NOTE: this is extremely crude
    txt = txt.replace("\\\n","\n")
    if txt.find('"""')>=0 :
        if txt.find("'''") != -1:
            raise ValueError("cannot deal with mixed multi-line notations in a single cell")
        keep_txt = _handle_multilinetext(txt,'"""')
    elif txt.find("'''")>=0 :
        if txt.find('"""') != -1:
            raise ValueError("cannot deal with mixed multi-line notations in a single cell")
        keep_txt = _handle_multilinetext(txt,"'''")
    else:
        keep_txt = [x for x in txt.split('\n') ]
    for i,entry in enumerate(keep_txt[:-1]):
        if(re.search('print(.*)',entry)):
            warnings.warn("print function found on a non-terminal line. Attempting to comment it out.")
            keep_txt[i] = re.sub(r'print\((.*)\)',r'# print(\1)',entry)
    kt2 = []
    for entry in keep_txt:
        if entry.startswith('#'):
            entry = []
        else:
            entry = re.split(r'\s#',entry)[0]
        if len(entry):
            if len(kt2) and entry[0] in ' \t':
                kt2[-1] = kt2[-1]+'\n... '+entry
                if kt2[-1].find('>>> ') in (0,1):
                    pass
                else:
                    if len(kt2)>1:
                        kt2[-1] = "\n>>> "+kt2[-1]
                    else:
                        kt2[-1] = ">>> "+kt2[-1]
            else:
                kt2.append(entry)
    keep_txt = kt2
    if not keep_txt:
        return None,None
    ktj = ";".join(keep_txt)
    if ktj[:4] != '>>> ':
        ktj = ">>> "+ktj
    cell_code = ktj
    outputs = [x for x in cell['outputs'] if x['output_type'] in ('execute_result','stream')]
    if len(outputs)>1:
        warnings.warn("more than one output found. Ignoring all but the last")
        outputs = outputs[-1:]

    cell_output=[]
    haveEllipsis=False
    for output in outputs:
        if output['output_type']=='execute_result':
            d = output['data']
            if 'text/plain' not in d:
                continue
            txt = d['text/plain']
        elif output['output_type']=='stream':
            if output['name'] == 'stdout':
                txt = output['text']
                txt = txt.replace('\n\n','\n<BLANKLINE>\n')
        else:
            raise NotImplementedError(output['output_type'])
        if ptr_expr.search(txt):
            txt = ptr_expr.sub(r'<\1... at 0x...>',txt)
            haveEllipsis = True
        if img_expr.search(txt):
            txt = img_expr.sub(r'<img src=...>',txt)
            haveEllipsis = True
        cell_output.append(txt)
    if haveEllipsis: cell_code += ' # doctest: +ELLIPSIS'
    return [cell_code],cell_output

def process_notebook(nb):
    """
    to fix:
      - multiple lines that produce output (i.e. non-final print lines!)
      - supporting ipython magic in cells
    """
    lines = []
    for cell in nb.cells:
        if cell['cell_type']=='code':
            cell_code,cell_output = process_cell(cell)
            if cell_code is None: continue
            lines.extend(cell_code)
            lines.extend(cell_output)
    return '\n'.join(lines)

import doctest

def rundoctests(text, name='<text>', globs=None, verbose=None,
               report=True, optionflags=None, extraglobs=None,
               raise_on_error=False,
               quiet=False,):
    # adapted from: http://www.mail-archive.com/python-list@python.org/msg404719.html
    # Assemble the globals.
    if optionflags is None:
        optionflags = doctest.NORMALIZE_WHITESPACE
    if globs is None:
        globs = globals()
    globs = globs.copy()
    if extraglobs is not None:
        globs.update(extraglobs)
    if '__name__' not in globs:
        globs['__name__'] = '__main__'
    # print(text)
    # Parse the text to find doc tests.
    parser = doctest.DocTestParser()
    test = parser.get_doctest(text, globs, name, name, 0)
    # Run the tests.
    if raise_on_error:
        runner = doctest.DebugRunner(
                verbose=verbose, optionflags=optionflags)
    else:
        runner = doctest.DocTestRunner(
                verbose=verbose, optionflags=optionflags)
    if quiet:
        runner.run(test, out=lambda s: None)
    else:
        runner.run(test)
    if report:
        runner.summarize()
    # Return a (named, if possible) tuple (failed, attempted).
    a, b = runner.failures, runner.tries
    try:
        TestResults = doctest.TestResults
    except AttributeError:
        return (a, b)
    return TestResults(a, b)

def run_tests(txt):
    res = rundoctests(txt)
    return res

if __name__ =='__main__':
    import sys
    nTried=0
    nFailed=0
    for fn in sys.argv[1:]:
        print("--------------------------------------------------------------")
        print("  TESTING:  %s"%fn)
        nb = _notebook_read(fn)
        txt = process_notebook(nb)
        tpl = run_tests(txt)
        nFailed += tpl.failed
        nTried += tpl.attempted
    if nFailed:
        print("FAILED: %d tests of %d run"%(nFailed,nTried))
        sys.exit(1)
    else:
        print("All %d tests passed"%nTried)
        sys.exit(0)
