# Guidelines for contributing a tutorial

The major guiding principle here is that it must be possible build the tutorials
and verify that they are correct in an automated way. This is to protect against
the inevitable "doc rot" that happens under any other circumstances.

## Python-based tutorials

These tutorials are written in [Jupyter](http://jupyter.org), which provides an
excellent interactive notebook work working with Python code. There's extensive
RDKit integration with Jupyter.

At the time of this writing (October 2016), there's no convenient way to
automatically run doctests in a Jupyter notebook that looks like a tutorial. I
created some code to work around this gap that is functional, but not perfect.
Many of the guidelines below are due to the limitations in that testing code.

### Guidelines

- Please follow the naming scheme of the other tutorials: `XXX_NAME.ipynb` where `XXX` is the zero-padded (to ensure proper sorting) number of the tutorial. The numbering should be sequential (except for the special-case of `999_Test1.ipynb`, which is there as part of the testing code).

- Include a markdown cell somewhere in the document, preferably at the beginning, with a list of tags that are appropriate for the tutorial. This should look like: `@TAGS: #basics #2D`. If you have a question about which tags are currently in use, just [search the repo](https://github.com/rdkit/rdkit-tutorials/search?q=%22%40TAGS%22&type=Code) for the text `@TAGS` and see what shows up. If a tag is missing that you think should be there, just use it. But please do try not to introduce redundant tags.

- If possible, avoid using the `print()` function. If you would like to show the output of a function/operation, just make that the last operation in a code cell; it will show up as the output and can then be properly tested. If you must include a `print()` function (because, for example, you'd like to show a multi-line string), make it the *last* line of the cell. The output of this `print()` will then be included in the tests. Other occurences of `print()` in a cell will be ignored when the tests are run.

- If you would like to include a code cell that is ignored by the tests, include the string `#doctest: IGNORE` somewhere in the block. Please use this sparingly and note that this code cell will not be executed *at all* when the tests are run, so don't include any imports, assignments, definitions, etc. in one of these cells that is required by other cells.
