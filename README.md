# Salvia

a python gnuplot 5 wrapper

# Installation

    python setup.py install

# Usage
~~~~
    import pandas as pd
    import numpy as np
    from Salvia import Gnuplot

    df = pd.DataFrame(np.random.randn(10, 4), columns=list('ABCD'))

    Gnuplot.draw(x="A", y=["B","C"], data=df, func="scatter")
~~~~

