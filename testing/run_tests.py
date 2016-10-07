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
import os,warnings
import nbformat

def _notebook_read(path):
    """Read a notebook using nbformat
    """
    inf = open(path)
    nb = nbformat.read(inf,nbformat.current_nbformat)
    return nb

import re
ptr_expr = re.compile(r'^<(.*) at 0x.*>')
def process_cell(cell):
    txt = cell['source']
    if not txt:
        return None,None
    if(re.search('print(.*)',txt)):
        warnings.warn("print functions found in a cell. Attempted to comment them out.")
    txt = re.sub(r'print\((.*)\)',r'# print(\1)',txt)

    cell_code = ['>>> '+x for x in txt.split('\n')]
    if len(cell['outputs'])>1:
        warnings.warn("Multiple outputs found for a cell. Only the execute_result will be used")
    outputs = [x for x in cell['outputs'] if x['output_type']=='execute_result']
    assert len(outputs)<=1
    cell_output=[]
    for output in outputs:
        d = output['data']
        if 'text/plain' not in d:
            continue
        txt = d['text/plain']
        if ptr_expr.match(txt):
            txt = ptr_expr.sub(r'<\1... at 0x...>',txt)
            cell_code[-1] += ' # doctest: +ELLIPSIS'
        cell_output.append(txt)

    return cell_code,cell_output

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
               report=True, optionflags=0, extraglobs=None,
               raise_on_error=False,
               quiet=False,):
    # adapted from: http://www.mail-archive.com/python-list@python.org/msg404719.html
    # Assemble the globals.
    if globs is None:
        globs = globals()
    globs = globs.copy()
    if extraglobs is not None:
        globs.update(extraglobs)
    if '__name__' not in globs:
        globs['__name__'] = '__main__'
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
