# Salvia

a python gnuplot 5 wrapper

create a figure
from Salvia import Gnuplot

Gnuplot.draw(x="Position", y="Temperature", data=df, func="line")
Gnuplot.Gridplot([f], "filename", show=True, style=lambda x:x)
