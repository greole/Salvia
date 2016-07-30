from collections import OrderedDict
import os
import time

rcParams = {
    'colors': ['#0072bd', '#d95319', '#edb120', '#7e2f8e', '#77ac30', '#4dbeee',
                '#a2142f'],
    'figure_width_px': 255,
    'figure_height_px': 255,
    'figure_width_cm': 5.75,
    'figure_height_cm': 5.75,
    'max_canvas_width_px': 600,
    'max_canvas_height_px': 386,
    'max_canvas_width_cm': 13.5,
    'max_canvas_height_cm': 8.74,
    'svg_font': 'Arial bold',
    'border': 31,
    'lw': 2,
    'lmargin': '0.1',
    'rmargin': '0.9',
    'tmargin': '0.9',
    'bmargin': '0.1',
    'spacing': '0.025',
    'y_label_offset': [0.02, 0],
    'x_label_offset': [0, 0],
}

class GnuplotFigure():

    def __init__(self, **kwargs):
        self.x = []
        self.y = []
        self.lt = []

        self.x_label = lambda: None
        self.x_label.text = kwargs.get("xlabel", "None")
        self.x_label.visible = True

        self.y_label = lambda: None
        self.y_label.text = kwargs.get("ylabel", "None")
        self.y_label.visible = True

        self.x_range = [None, None]
        self.x_log = False

        self.y_range = [None, None]
        self.y_log = False

        # http://stackoverflow.com/questions/2827623
        self.legend = lambda: None
        self.legend.orientation = False
        self.legend.visible = True

        self.lw = 2
        self.title = "TEST"
        self.legends = []

    def add(self, x, y, legend, lt, plotProperties=None):
        self.legends.append(legend)
        self.x.append(x)
        self.y.append(y)
        self.lt.append(lt)


    @property
    def xrange(self):
        if list(map(lambda x: x != None, self.x_range))[0]:
            return self.x_range
        else:
            return [min([min(x) for x in self.x if len(x)]),
                    max([max(x) for x in self.x if len(x)])]

    @property
    def yrange(self):
        def valid_(y):
            if y is None:
                return False
            else:
                return len(y)


        if list(map(lambda x: x != None, self.y_range))[0]:
            return self.y_range
        else:
            return [min([min(y) for y in self.y if valid_(y) ]),
                    max([max(y) for y in self.y if valid_(y) ])]


    def pre_text(self):
        pass

    def text(self, interOpts=None, finalOpts=None):

        def lt(arg):
            return ("lp" if arg == "line" else "p")

        def dist(i):
            return int(len(self.x[i])/10)

        entries = ["_{} title '{}' w {} pt {} pi {} lw {} dashtype {}".format(
                   i, self.legends[i], lt(self.lt[i]), i+1, dist(i), rcParams['lw'], i+1)
                   for i, _ in enumerate(self.x)]

        return [" ${}" + e for e in entries]

    def _repr_svg_(self):
        mP = GnuplotMultiplot([self])
        return mP._repr_svg_()

class GnuplotMultiplot():
    # data is a OrderedDict of the form
    # {"id": [ GnuplotDataSet  ]}
    # self.data = OrderedDict()
    def __init__(self, data, filename=None, **kwargs):
        """ write gnuplot script given a list of gnuplot figures and a filename """

        self.filename = (filename if filename else self.generateFilename())
        if isinstance(data, list):
            dataOD = OrderedDict()
            for i, k in enumerate(data):
                dataOD.update({"i" + str(i): k})
            self.data = dataOD
        else:
            self.data = data

        n_sub_figs = len(self.data.items())
        self.istransposed = False

        self.n_sub_figs = (
                greatest_divisor(n_sub_figs),
                n_sub_figs/greatest_divisor(n_sub_figs))


        self.write_file()

    def write_file(self):
        with open(self.filename + "-svg.gp", 'w+') as f:
            fn = os.path.basename(self.filename)
            x, y = self.compute_fig_size_px()
            f.write(self.header(".svg").format(x, y, fn))
            self.write_body(self.data, f, self.n_sub_figs)

        with open(self.filename + ".gp", 'w+') as f:
            x, y = self.compute_fig_size_cm()
            fn = os.path.basename(self.filename)
            f.write(self.header(".eps").format(x, y, fn))
            self.write_body(self.data, f, self.n_sub_figs)

        cmd = "cd " + os.path.dirname(self.filename) + "; gnuplot " + os.path.basename(self.filename) + "-svg.gp"
        os.system(cmd)
        os.system("cd " + os.path.dirname(self.filename) + "; gnuplot " + os.path.basename(self.filename) + ".gp")


    def compute_fig_size_px(self):
        ny, nx = self.n_sub_figs
        if not self.istransposed:
            x = min(rcParams['figure_width_px']*nx, rcParams['max_canvas_width_px'])
            y = min(rcParams['figure_height_px']*ny, rcParams['max_canvas_height_px'])
        elif self.istransposed and nx == 1:
            # Extend to full canvas size if transposed and single column
            x = rcParams['max_canvas_width_px']
            y = min(rcParams['figure_height_px']*ny, rcParams['max_canvas_height_px'])
        return x, y


    def compute_fig_size_cm(self):
        ny, nx = self.n_sub_figs
        if not self.istransposed:
            x = min(rcParams['figure_width_cm']*nx, rcParams['max_canvas_width_cm'])
            y = min(rcParams['figure_height_cm']*ny, rcParams['max_canvas_height_cm'])
        elif self.istransposed and nx == 1:
            # Extend to full canvas size if transposed and single column
            x = rcParams['max_canvas_width_cm']
            y = min(rcParams['figure_height_cm']*ny, rcParams['max_canvas_height_cm'])
        return x, y

    def transpose(self):
        x, y = self.n_sub_figs
        self.n_sub_figs = (y, x)
        if not self.istransposed:
            self.istransposed = True
        else:
            self.istransposed = False


    def generateFilename(self):
        return "/tmp/SalviaPlot-" + str(time.time()).split('.')[0]

    def header(self, ext):
        if ext == ".svg":
            font = "fname '{}'".format(rcParams['svg_font'])
            return "set terminal svg enhanced size {}, {} " + font + "\nset output '{}.svg'\n"
        if ext == ".eps":
            # return "set terminal epslatex color size {}cm, 5.75cm \nset out '{}.eps'\n"
            return "set terminal epslatex monochrome size {}cm, {}cm ',bx'\nset out '{}.eps'\n"

    def write_body(self, data, f, n_sub_figs):

            def lt(arg):
                return ("lp" if arg == "line" else "p")


            margins = ",".join([rcParams[_ + "margin"] for _ in ['l','r','t','b']])
            f.write("set multiplot layout {}, {} margins screen {} spacing {}\n".format(
                n_sub_figs[0], n_sub_figs[1], margins, rcParams['spacing']))

            f.write("set border {} lw {}\n".format(
                    rcParams['border'], rcParams['lw']
                ))

            data_blocks, invalids = self.str_inline_data_blocks(data)
            f.write(data_blocks)

            for pid, d in data.items():
                pid = pid.replace("(", "").replace(")","")

                f.write("\nset xrange [{:.4g}: {:.4g}]\n".format(d.xrange[0], d.xrange[1]))
                f.write("\nset yrange [{:.4g}: {:.4g}]\n".format(d.yrange[0], d.yrange[1]))
                f.write(self.str_x_label(d.x_label))
                if d.x_log:
                    f.write("set logscale x\n")
                if d.y_log:
                    f.write("set logscale y\n")
                if d.legend.orientation and d.legend.visible:
                    f.write("set key " + d.legend.orientation + "\n")
                if d.legend.visible:
                    f.write("set key\n")
                else:
                    f.write("unset key")

                f.write(self.str_y_label(d.y_label))
                f.write("\nplot ")

                data_blocks = [e.format(pid) for e in d.text()]

                s = ("".join(intersperse(", ", data_blocks)))

                f.write(s)
            f.write("\nunset multiplot")

    def str_inline_data_blocks(self, data):
        """  write data directly into  gnuplot script and mark invalids"""
        invalids = {}
        ret = ""
        for pid, d in data.items():
            for i, (x, y) in enumerate(zip(d.x, d.y)):
                try:
                    x_ = (x if isinstance(x, tuple) else x.values)
                    y_ = y.values
                    if not len(y_):
                        invalids[pid, i] = True
                        continue
                    pid = pid.replace("(", "").replace(")", "")
                    ret += "${}_{} << EOD\n".format(pid, i)
                    for j in range(len(y)):
                        ret += "{} {} \n".format(x_[j], y_[j])
                    ret += "EOD\n"
                except Exception as e:
                    invalids[pid, i] = True
        return ret, invalids


    def str_x_label(self, x, options=None):
        if not x.visible:
            return ""
        options = " " + options if options else ""
        off = rcParams['x_label_offset']
        return "\nset xlabel \"{}\" offset screen {}, {}{}\n".format(
                x.text, off[0], off[1], options)

    def str_y_label(self, x, options=None):
        if not x.visible:
            return ""
        options = " " + options if options else ""
        off = rcParams['y_label_offset']
        return "\nset ylabel \"{}\" offset screen {}, {}{}\n".format(
                x.text, off[0], off[1], options)

    def _repr_svg_(self):
        self.write_file()
        return open(self.filename + ".svg", 'r').read()

# example colors
# https://www2.uni-hamburg.de/Wiss/FB/15/Sustainability/schneider/gnuplot/colors.htm
colored = rcParams['colors']

def greatest_divisor(number):
    if number == 1:
        return 1
    for i in reversed(range(number)):
        if number % i == 0:
            return i
    else:
        return 1

intersperse = lambda e, l: sum([[x, e] for x in l], [])[:-1]

def draw(x, y, data, title=None, func="line",
        z=None, figure=None, legend_prefix="", titles=None,
        names=None, **kwargs):
    """ draws a figure from x and y label and a dataframe
        if figure is given dataset will be drawn into existing figure
    """
    pP = kwargs.get('properties', False)

    figure = figure if figure else GnuplotFigure()
    y = (y if isinstance(y, list) else [y])
    for yi in y:
        x_data, y_data = data[x], data[yi]

        # First check explicitly specified name
        name = kwargs.get("name", None)

        # If no name given but properties
        if (not name and pP):
            name = pP.name
        else:
            name = "None"

        figure.add(
                x=x_data, y=y_data,
                legend=legend_prefix + name,
                lt=func)
    return figure

class LableSettr():

    def __init__(self, axis, field, figure, properties):
        label = kwargs.get(axis + '_label', False)
        if label:
            properties.plot_properties.insert(
                field, {axis + '_label': label})
        else:
            label = properties.plot_properties.select(
                field, axis + '_label', "None")
        setattr(figure, ax + '_label', label)

    def _range(axis, field):
        Range1d = []
        p_range_args = kwargs.get(axis + '_range', False)
        if p_range_args:
            properties.plot_properties.insert(
                field, {axis + '_range': p_range})
        else:
            p_range = properties.plot_properties.select(
                field, axis + '_range')
        if not p_range:
            return False
        else:
            Range1d.append(p_range[0])
            Range1d.append(p_range[1])
            return Range1d

    def _log(axis, field):
        try:
            p_range = properties.plot_properties.select(
                field, axis + '_log')
            return p_range
        except:
            return False
