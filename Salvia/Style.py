class TemplateMargins():

    @classmethod
    def singlePlot(cls):
        return {'lmargin': 0.35}

class Styler():

    def __init__(self, func, slyce=None, prev=None):
        self.slyce = slyce
        self.prev = prev
        self.func = func

    def __call__(self, figures):
        if self.prev:
           figures = self.prev.__call__(figures)
        figures_items = figures.data.items()
        self.iterate(figures_items)
        return figures

    def _repr_svg_(self):
        return self.figures._repr_svg_()

    def iterate(self, figures):
        figures = list(figures)[self.slyce] if self.slyce else figures

        for i, f in figures:
            self.func(f)

def chain(Self, *obj):
    if len(obj) > 1:
        for i, o in enumerate(obj[1:]):
            setattr(obj[i+1], "prev", obj[i])
    return obj[-1]


class CleanAxis(Styler):

    def __init__(self, name, slyce=None, prev=None):
        self.name = name
        Styler.__init__(self, func=self.func, slyce=slyce, prev=prev)

    def func(self, figure):
        _label = getattr(figure, self.name + "_label")
        setattr(_label, "visible", False)
        setattr(_label, "name", "")
        setattr(_label, "exp_format", "")

class Legend(Styler):

    def __init__(self, pos, slyce=None, prev=None):
        self.pos = pos
        Styler.__init__(self, func=self.func, slyce=slyce, prev=prev)

    def func(self, figure):
        obj = getattr(figure, "legend")
        setattr(obj, "orientation", self.pos)

class CleanColormaps(Styler):

    def __init__(self, slyce=None, prev=None):
        Styler.__init__(self, func=self.func, slyce=slyce, prev=prev)

    def func(self, figure):
        attr = getattr(figure, "pre_set")
        attr.append("unset colorbox\n")
        # attr = getattr(figure, "post_set")
        # attr.append("set colorbox\n")

class CleanLegend(Styler):

    def __init__(self, slyce=None, prev=None):
        Styler.__init__(self, func=self.func, slyce=slyce, prev=prev)

    def func(self, figure):
        obj = getattr(figure, "legend")
        setattr(obj, "visible", False)


class BgColor(Styler):

    def __init__(self, color, slyce=None, prev=None):
        self.color=color
        Styler.__init__(self, func=self.func, slyce=slyce, prev=prev)

    def func(self, figure):
        attr = getattr(figure, "pre_set")
        attr.append(" ".format(self.color))
        attr = getattr(figure, "post_set")
        attr.append("set background rgb white\n")

