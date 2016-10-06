import os,warnings
import nbformat

def _notebook_read(path):
    """Read a notebook via nbconvert
       :returns parsed nb object
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
    # From: http://www.mail-archive.com/python-list@python.org/msg404719.html
    # Assemble the globals.
    if globs is None:
        globs = globals()
    globs = globs.copy()
    if extraglobs is not None:
        globs.update(extraglobs)
    if '__name__' not in globs:
        globs['__name__'] = '__main__'
    # Parse the text looking for doc tests.
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
    for fn in sys.argv[1:]:
        nb = _notebook_read(fn)
        txt = process_notebook(nb)
        print(txt)
        run_tests(txt)
