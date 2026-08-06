"""
Generated KurimaSense documents.

The four documents this package will produce — Season Evidence Pack, portfolio
report, field report, season plan — share one property that shapes everything
here: **they leave the building**. A contractor forwards a pack to a leaf buyer;
a lender files a report. Once sent, it cannot be re-rendered or corrected.

That is why the design system is code and not a set of templates to copy:

  ``tokens.py``      colours, type scale, spacing — the single source
  ``stylesheet.py``  the CSS, generated from those tokens
  ``identity.py``    the mark, the issue number, the verification line
  ``render.py``      template + data -> PDF (the only module that does I/O)
  ``templates/``     one file per document, all extending ``base.html``

Everything except ``render.py`` is pure and importable without WeasyPrint, so
the parts that decide what a document *claims* are unit-tested in a bare
container.
"""
