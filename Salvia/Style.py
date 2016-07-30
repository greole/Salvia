class Styler():

    def __init__(self, func, slyce=None, prev=None):
        self.slyce = slyce
        self.prev = prev
        self.func = func

    def __call__(self, figures):
        figures_items = figures.data.items()
        if self.prev:
           self.iterate(self.prev.__call__(figures_items))
        else:
            self.iterate(figures_items)
        self.figures = figures
        return self

    def _repr_svg_(self):
        return self.figures._repr_svg_()

    def iterate(self, figures):
        figures = list(figures)[self.slyce] if self.slyce else figures
        for i, f in figures:
            self.func(f)


class CleanYAxis(Styler):

    def __init__(self, slyce=None, prev=None):
        Styler.__init__(self, func=self.func, slyce=slyce, prev=prev)

    def func(self, figure):
        y_label = getattr(figure, "y_label")
        setattr(y_label, "visible", False)

class CleanLegend(Styler):

    def __init__(self, slyce=None, prev=None):
        Styler.__init__(self, func=self.func, slyce=slyce, prev=prev)

    def func(self, figure):
        obj = getattr(figure, "legend")
        setattr(obj, "visible", False)
