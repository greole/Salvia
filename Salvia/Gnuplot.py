from collections import OrderedDict
import subprocess
from itertools import cycle
import os
import time
import re
from binascii import b2a_hex, b2a_base64, hexlify



NumberTypes = (int, float, complex)

color_palette = [
    # '#0000ff', # blue
    # '#007f00', # green
    # '#ff0000', # red
    # '#00bfbf', # cyan
    # '#bf00bf', # pink
    # #'#bfbf00,  # yellow
    # '#3f3f3f', # black]
     '#000080',  # blue
     '#ff0000',  # red
     '#ff8000',  # orange
     '#000000',  # black
     '#88dd88',  # light green
     '#7e2f8e',  # purple
     '#ff8080',  # lighter red
     # '#ffbf80', # lighter orange

     '#000000',  # black
     '#88dd88',  # light green
     '#4dbeee',  # light-blue
     "#48D1CC",  # light green

     '#ff8080',  # lighter red
     '#4242d7',  # lighter blue
     '#0080ff',  # light blue
     "#98FB98",
     # '#d95319', # orange
       # '#FF4500',# brown
     # '#77ac30', # green
    #'#0000ff',#
    #'#007f00', # green
    # '#ffff00',#
    #'#80ff80',#
    #'#00ffff',#
#  '#0072bd', # blue
#  '#edb120', # yellow
#  '#a2142f', # red
    ]

rcParams = {
    'colors': color_palette,
    'figure_width_px': 255,
    'figure_height_px': 255,
    'figure_width_cm': 5.75,
    'figure_height_cm': 5.75,
    'max_canvas_width_px': 750,
    'max_canvas_height_px': 250,
    'max_canvas_width_cm': 13.5,
    'max_canvas_height_cm': 5.4,
    'svg_font': 'Arial bold',
    'border': 31,
    'lw': 1,
    'lmargin': '0.1',
    'rmargin': '0.9',
    'tmargin': '0.9',
    'canvas_bmargin': '0.2',
    'canvas_lmargin': '0.2',
    'canvas_rmargin': '0.8',
    'canvas_tmargin': '1.0',
    'spacing': '0.025',
    'y_label_offset': [0.0, 0],
    'y2_label_offset': [0.0, 0],
    'x_label_offset': [0, 0],
    'xformat': '%g',
    'yformat': '%g',
    'y2format': '%g',
    'num_y_tics': 3,
    'num_y2_tics': 3,
    'num_x_tics': 3,
    'num_x2_tics': 3,
    'plot_size': [],
    'plot_ratio': 1.0,
    'eps_terminal_options': 'color',
    'svg_terminal_options': '',
    'png_terminal_options': '',
    'legend_position': 'top right',
    'exp_line_width': 1,
}

class RcParams(dict):
    """ hold local rcParams and delegate to global """

    def __getitem__(self, key):
        if key in self:
            return super(RcParams, self).__getitem__(key)
        else:
            return rcParams.get(key, None)


class PlotProperty():
    """ Base class holding properties of a plot which
        are usually specified by set and unset commands """

    @property
    def text(self):
        pass

    @property
    def post_text(self):
        pass


class Grid(PlotProperty):

    def __init__(self, canvas=None, visible=True):
        self.visible = visible

    @property
    def text(self):
        if self.visible:
            return "set grid\n"
        else:
            return ""

    @property
    def post_text(self):
        if self.visible:
            return "unset grid\n"
        else:
            return ""


class Label(PlotProperty):

    def __init__(self, axis, text, svg, canvas=None, visible=True):
        self.axis = axis
        self.axis_normalised = axis.replace("2", "")
        self.name = text
        self.canvas = canvas
        self.visible = visible
        self.exp_format = None
        self.exp_offset = None
        self.exp_tics  = None
        self.svg = svg

    @property
    def _format(self):
        """ Order
                1. size given explicitly via constructor
                2. size from canvas
                3. rcParams
        """
        pre = 'set format {} "{}"\n'
        if isinstance(self.exp_format, str):
            val = self.exp_format
        elif self.canvas:
            val = self.canvas._format(self.axis)
        else:
            val = rcParams[self.axis + "format"]
        return pre.format(self.axis, val)

    @property
    def _offs(self):
        """ Order
                1. size given explicitly via constructor
                2. size from canvas
                3. rcParams
        """
        if isinstance(self.exp_offset, list):
            val = self.exp_offset
        elif self.canvas:
            val = self.canvas._offs(self.axis)
        else:
            val = rcParams[self.axis + "_label_offset"]
        return val

    def tics(self, _range):
        if self.exp_tics:
            val = self.exp_tics
        elif self.canvas:
            val = self.canvas._tics(self.axis)
        else:
            val = rcParams["num_{}_tics".format(self.axis)]
        if (not isinstance(_range[0], NumberTypes)
            or not isinstance(_range[1], NumberTypes)):
            return ""
        l = _range[0]
        u = _range[1]
        tics = abs((u - l)/val)
        return "set {}tics {}, {}, {}\n".format(self.axis, min(l,u), tics, 0.9*max(l,u))

    def text(self, svg):
        if not self.visible:
            return 'set format {} ""\n'.format(self.axis)
        off = self._offs
        pre = self._format
        # TODO clean latex commands from text if in svg mode
        if svg:
            name = self.name.replace("$", "")
            name = name.replace("overline", "")
        else:
            name = self.name.replace("\\", "\\\\")
            name = "\\\\shortstack{" + name + "}"
        return pre + "set {}label \"{}\" offset screen {}, {}\n".format(
                self.axis, name, off[0], off[1])

    @property
    def post_text(self):
        if self.visible:
            return 'set {}label ""\n'.format(self.axis)
        else:
            return ""


class Size(PlotProperty):

    def __init__(self, ratio=None, size=None, canvas=None):
        self.exp_ratio = ratio
        self.exp_size = size
        self.canvas = canvas

    @property
    def size(self):
        """ Order
                1. size given explicitly via constructor
                2. size from canvas
                3. rcParams
        """
        if self.exp_size:
            return self.exp_size
        if self.canvas:
            return self.canvas.plot_size
        return rcParams["plot_size"]

    @property
    def ratio(self):
        """ Order
                1. size given explicitly via constructor
                2. size from canvas
                3. rcParams
        """
        if self.exp_size:
            return self.exp_ratio
        if self.canvas:
            return self.canvas.plot_ratio
        return rcParams["plot_ratio"]

    @property
    def text(self):
        return "set size ratio {} {}\n".format(
                self.ratio, " ".join(map(str, self.size)))


class Legend(PlotProperty):

    def __init__(self, orientation=None, canvas=None):
        self.visible = True
        self.orientation = orientation
        self.canvas = canvas
        self.legends = []

    @property
    def text(self):
        if not self.visible:
            return "unset key\n"
        t = "set key {}\n"
        if self.orientation:
            val = self.orientation
        elif self.canvas:
            val = self.canvas.orientation
        else:
            val = rcParams["legend_position"]
        return t.format(val)

    def __getitem__(self, i):
        return self.legends[i]


class TextLabels(list):

    @property
    def text(self):
        o = ""
        for i, t in enumerate(self):
            o += "set label {} {}\n".format(i+1, t)
        return o

    @property
    def post_text(self):
        o = ""
        for i, t in enumerate(self):
            o += "unset label {}\n".format(i+1)
        return o


class Line():

    def __init__(self, canvas=None):
        self.exp_withs = [] # line or points
        self.exp_line_types = None
        self.exp_line_color = []
        self.exp_line_width = None
        self.exp_dashtype = None
        self.exp_pointtype = None
        self.ctr = self.gen()
        self.canvas = canvas

    def get(self, i, palette):
        return "w {wt} pt {pt} dt {dt} lw {lw} {lc}".format(
                wt=self._with(i, palette),
                lw=self._line_width(i),
                pt=self._pointtype(i),
                dt=self._dashtype(i),
                lc=self._color(i, palette))

    def _prop(self, name, i):
        prop = getattr(self, name)
        if isinstance(prop, list) and prop[i]:
            val = prop[i]
            val = val if val != "quad" else "line"
            val = val if val != "scatter" else "points"
        elif isinstance(prop, str):
            val = prop
        elif self.canvas:
            val = self.canvas.rcParams[name]
        else:
            val = rcParams.get(name, False)
        return val

    def _with(self, i, palette):
        return self._prop("exp_withs", i) + palette

    def gen(self):
        # l = []
        # for i in range(40):
        #      for _ in range(3):
        #         l.append(i)
        # for i in cycle(l):
        #     yield i
        # NOTE this counter is called several times per figure
        # e.g. for line color, point and dash types
         def init():
             return 0
         i = init()
         while True:
             for _ in range(3):
                 val = (yield i)
             if val=='restart':
                 print("DEBUG gen reset")
                 i = 0 # init()
             else:
                 # print("DEBUG ctr incr", i)
                 i += 1

    def _color(self, i, palette=False):
        if palette:
            return ""
        val = self.exp_line_color[i]  #False #self._prop("exp_color", i)
        colors = rcParams["colors"]
        num_cols = len(colors)
        index = val
        if not val:
            index = int(next(self.ctr)) % num_cols
        elif isinstance(val, int):
            index = val
            val = False
        ret = val if val else colors[index]
        return "lc rgb '" + ret + "'"

    def _line_width(self, i):
        return str(self._prop("exp_line_width", i))

    def _dashtype(self, i):
        prop = self._prop("exp_dashtype", i)
        index = int(next(self.ctr))
        prop = prop if prop else str(index+ 1)
        return prop

    def _pointtype(self, i):
        prop = self._prop("exp_pointtype", i)
        index = int(next(self.ctr))
        prop = prop if prop else str(index + 1)
        return prop

    def append(self, lt, exp_color=False):
        self.exp_withs.append(lt)
        self.exp_line_color.append(exp_color)


class GnuplotFigure():

    def __init__(self, **kwargs):

        self.rcParams = RcParams(kwargs.get("rcParams", dict()))
        self.svg = False

        self.x = []
        self.y = []
        self.z = []

        self.canvas = kwargs.get("canvas", None)

        self.filename = kwargs.get("filename", None)

        self.lt = Line(self.canvas)

        # self.labels = TextLabels()
        self.labels = TextLabels()

        self.x_label = Label("x", kwargs.get("xlabel", "None"), self.svg, self.canvas)
        self.x2_label = Label("x2", kwargs.get("xlabel", "None"), self.svg, self.canvas)

        self.y_label = Label("y", kwargs.get("ylabel", "None"), self.svg, self.canvas)
        self.y2_label = Label("y2",
                kwargs.get("y2label", "None"),
                self.svg, self.canvas, visible=False)

        self.size = Size(
                kwargs.get("ratio", None),
                kwargs.get("size", None),
                self.canvas)

        self.x_range = [None, None]
        self.x2_range = [None, None]
        self.x_log = False

        self.y_range = [None, None]
        self.y2_range = [None, None]
        self.y_log = False

        self.grid = Grid(self.canvas, visible=True)

        # http://stackoverflow.com/questions/2827623
        self.legend = Legend()

        self.title = "TEST"
        self.pre_set = []
        self.post_set = []

    def reset_ctr(self):
        #TODO FIXME
        # print("DEBUG ctr reset")
        self.lt.ctr.send("restart")


    def insert(self, f2):
        for i in range(len(f2.x)):
            self.legend.legends.append(f2.legend.legends[i])
            self.x.append(f2.x[i])
            self.y.append(f2.y[i])
            self.z.append(f2.z[i])
            self.lt.append(f2.lt.exp_withs[i])
        return self

    def add(self, x, y, legend, lt, z=None, plotProperties=None):
        self.legend.legends.append(legend)
        self.x.append(x)
        self.y.append(y)
        self.z.append(z)
        self.lt.append(lt)

    @property
    def vals(self):
        if self.z:
            return (self.x, self.y, self.z)
        else:
            return (self.x, self.y)

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

        def min_(y):
            try:
                return min(y)
            except:
                print(y)
                return False

        def max_(y):
            try:
                return max(y)
            except:
                return False


        if list(map(lambda x: x != None, self.y_range))[0]:
            return self.y_range
        else:
            minys = [min_(y) for y in self.y]
            maxys = [max_(y) for y in self.y]
            return [min([y for y in minys if isinstance(y, NumberTypes)]),
                    max([y for y in maxys if isinstance(y, NumberTypes)])]

    def set(self, opts, undo=True):
        self.pre_set.append("set " + opts + "\n")
        if undo:
            self.post_set.append("unset " + opts + "\n")

    def unset(self, opts, undo=True):
        self.pre_set.append("unset " + opts + "\n")
        if undo:
            self.post_set.append("set " + opts + "\n")


    def pre_text(self, svg):
        self.svg = svg

        # TODO use pre_set more extensivly
        pre_set = "".join(self.pre_set)

        return "".join([
                    self.size.text,
                    self.legend.text,
                    self.labels.text,
                    self.x_label.tics(self.x_range),
                    self.y_label.tics(self.y_range),
                    self.y2_label.tics(self.y_range),
                    self.x_label.text(svg),
                    self.y_label.text(svg),
                    self.y2_label.text(svg),
                    self.grid.text,
                    pre_set])

    def ftext(self, interOpts=None, finalOpts=None):

        def lt(arg):
            return ("lp" if arg == "line" else "p")

        def dist(i):
            try:
                return int(len(self.x[i])/10)
            except:
                return 1

        palette = lambda i: "" if isinstance(self.z[i], type(None)) else " palette"
        # entries = ["_{} title '{}' w {} {} pt {} pi {} lw {} dashtype {}".format(
        #            i, self.legend[i], lt(self.lt[i]), palette(i), i+1, dist(i)
        #            , self.rcParams['lw'], i+1)
        #            for i, _ in enumerate(self.x)]

        entries = ["_{} title '{}' {} pi {}".format(
                   i, self.legend[i], self.lt.get(i, palette(i)), dist(i))
                   for i, _ in enumerate(self.x)]

        return [" ${}" + e for e in entries]

    def text(self):
        self.reset_ctr()
        return GnuplotMultiplot([self], filename=self.filename).text()

    def post_text(self):
        post_set = "".join(self.post_set)
        return "".join([
                    post_set,
                    "\n",
                    self.labels.post_text,
                    self.y_label.post_text,
                    self.y2_label.post_text,
                    self.x_label.post_text,
                    self.x2_label.post_text,
                    self.grid.post_text,
                    "\nunset xtics",
                    "\nunset ytics\n"])

    #def _repr_svg_(self):
    #    self.reset_ctr()
    #    mP = GnuplotMultiplot([self], filename=self.filename)
    #    mP.write_file()
    #    return mP._repr_svg_()

    def _repr_png_(self):
        self.reset_ctr()
        mP = GnuplotMultiplot([self], filename=self.filename)
        mP.write_file()
        return mP._repr_png_()


class GnuplotScript():

    def __init__(self, script, filename=None):

        self.filename = (filename if filename else self.generateFilename())
        self.script = script
        self.svg=False

    def write_script_to_file(self, header, ext=".gp"):
        with open(self.filename + ext, 'w+') as f:
            f.write(header)
            f.write(self.script)

    def generateFilename(self):
        return "/tmp/SalviaPlot-" + str(time.time()).split('.')[0]

    def change_terminal(self, terminal, file_ext):
        self.script = re.sub(
            "(?<=set terminal )[A-Za-z0-9\.]+(?=\n)",
            "set terminal " + terminal + "\n", self.script)

        filename = re.findall("set output[ ]+'([A-Za-z]+)[A-Za-z.]+'\n", self.script)[0]
        self.script = re.sub(
            "set output[ ]+'[A-Za-z]+([A-Za-z.]+)'\n",
            "set output '{}.{}'\n".format(filename, file_ext),
            self.script)


    def call_gnuplot(self, svg=False, ext="_eps.gp"):
        self.svg = svg
        cmd = "{}".format(os.path.basename(self.filename)) + ext
        cwd = os.path.dirname(self.filename)
        if cwd == '':
            cwd = './'
        try:
            self.gnuplot_output = subprocess.check_output(["gnuplot", cmd],
                    cwd=cwd, stderr=subprocess.PIPE)
        except Exception as e:
            print("cmd gnuplot {} in {} failed ".format(cmd,cwd))
            print(e)

    #def _repr_svg_(self):
    #    self.call_gnuplot(svg=True, ext="_svg.gp")
    #    print("Displaying file: {}{}".format(self.filename, ".svg"))
    #    return open(self.filename + ".svg", 'r').read()

    def _repr_png_(self):
        self.call_gnuplot(svg=True, ext="_png.gp")
        fn = "{}{}".format(self.filename, ".png")
        print("Displaying file: " + fn)
        data = b2a_base64(open(fn, 'rb').read()).decode("ascii").replace("\n","")
        return data


def from_script(script):
    filename = "/tmp/" + re.findall("set output[ ]+'([A-Za-z]+)[A-Za-z.]+'\n", script)[0]
    sc = GnuplotScript(script, filename)
    sc.write_script_to_file("")
    return sc

class GnuplotMultiplot(GnuplotScript):
    # data is a OrderedDict of the form
    # {"id": [ GnuplotDataSet  ]}
    # self.data = OrderedDict()
    def __init__(self, data, filename=None, **kwargs):
        """ write gnuplot script given a list of gnuplot figures and a filename """

        super(GnuplotMultiplot, self).__init__("", filename)
        self.rcParams = RcParams(kwargs.get("rcParams", dict()))
        self.title = False

        if isinstance(data, list):
            dataOD = OrderedDict()
            for i, k in enumerate(data):
                dataOD.update({"i" + str(i): k})
            self.data = dataOD
        else:
            self.data = data

        self.istransposed = kwargs.get("transposed", False)
        self.flat = kwargs.get("flattened", False)

        self.set_style = None
        # TODO refactor this
        # set canvas references
        self.style = kwargs.get("style", False)

    def reset_ctrs(self):
        # TODO FIXME
        for _, fig in self.data.items():
            fig.reset_ctr()

    def set_canvas(self):
        for _, fig in self.data.items():
            setattr(fig, "canvas", self)
            for name in ["size", "x_label", "y_label", "y2_label", "legend", "lt"]:
                attr = getattr(fig, name)
                setattr(attr, "canvas", self)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key, GnuplotFigure())

    def display(self, displ):
        self.call_gnuplot(svg=True, ext="_png.gp")
        fn = "{}{}".format(self.filename, ".png")
        displ(fn)

    @property
    def n_sub_figs(self):
        n_sub_figs = len(self.data.items())
        if not self.flat:
            x, y = (greatest_divisor(n_sub_figs),
                    n_sub_figs/greatest_divisor(n_sub_figs))
        else:
            x, y = (n_sub_figs, 1)

        if self.istransposed:
            return y, x
        else:
            return x, y

    def insert(self, m2):
        own_keys = list(self.data.keys())
        rem_keys = list(m2.data.keys())
        for i, (k, d) in enumerate(m2.data.items()):
            self.data[own_keys[i]].insert(d)

    def intersperse(self, m2):
        dataOD = OrderedDict()
        for ((k1, d1), (k2, d2)) in zip(m2.data.items(), self.data.items()):
            dataOD.update({k2+"1": d2})
            dataOD.update({k1+"2": d1})
        return GnuplotMultiplot(dataOD, self.filename)

    @property
    def plot_size(self):
        return self.rcParams["plot_size"]

    @property
    def plot_ratio(self):
        return self.rcParams["plot_ratio"]

    def _offs(self, axis):
        return self.rcParams[axis + "_label_offset"]

    def _format(self, axis):
        return self.rcParams[axis + "format"]

    def _tics(self, axis):
        return self.rcParams["num_" + axis + "_tics"]

    @property
    def orientation(self):
        return self.rcParams["legend_position"]

    def update_legends(self, legends):
        for i, f in self.data.items():
            l = getattr(f, "legend")
            setattr(l, "legends", legends)

    def update_legends_orientation(self, orientation):
        for i, f in self.data.items():
            l = getattr(f, "legend")
            setattr(l, "orientation", orientation)

    def update_labels(self, axis, prop, labels):
        for i, (_, f) in enumerate(self.data.items()):
            l = getattr(f, axis  + "_label")
            setattr(l, prop, labels[i])

    def update_(self, obj, labels):
        for i, (_, f) in enumerate(self.data.items()):
            l = getattr(f, obj)
            setattr(l, "name", labels[i])


    def set_visibility(self, name, vis_map):
        for i, (_, f) in enumerate(self.data.items()):
            l = getattr(f, name)
            setattr(l, "visible", vis_map[i])

#    def _repr_svg_(self):
#        # TODO build a svg variant of the figure
#        self.write_file()
#        return super(GnuplotMultiplot, self)._repr_svg_()

    def _repr_png_(self):
        # TODO build a svg variant of the figure
        self.write_file()
        return super(GnuplotMultiplot, self)._repr_png_()


    def write_file(self):
        self.set_canvas()

        # Style before write
        if self.style:
            self.style(self)

        # Export to eps
        x, y = self.compute_fig_size_cm()
        fn = os.path.basename(self.filename)
        opts = self.rcParams['eps_terminal_options']
        self.script = self.text(svg=False)
        self.write_script_to_file(self.header(".eps").format(x, y, opts, fn), "_eps.gp")
        self.call_gnuplot()
        self.reset_ctrs()

        # with open(self.filename + "-svg.gp", 'w+') as f:
        fn = os.path.basename(self.filename)
        x, y = self.compute_fig_size_px()
        opts = self.rcParams['svg_terminal_options']
        self.script = self.text(svg=True)
        self.write_script_to_file(self.header(".svg").format(x, y, opts, fn), "_svg.gp")
        self.call_gnuplot(svg=True)
        self.reset_ctrs()

        # Export to png
        fn = os.path.basename(self.filename)
        x, y = self.compute_fig_size_px()
        opts = self.rcParams['png_terminal_options']
        self.script = self.text(svg=True)
        self.write_script_to_file(self.header(".png").format(x, y, opts, fn), "_png.gp")
        self.call_gnuplot(svg=True)
        self.reset_ctrs()

    def compute_fig_size_px(self):
        """
        ny, nx = self.n_sub_figs
        if not self.istransposed:
            x = min(self.rcParams['figure_width_px']*nx,
                    self.rcParams['max_canvas_width_px'])
            y = min(self.rcParams['figure_height_px']*ny,
                    self.rcParams['max_canvas_height_px'])
        """
        heighIncr = 0 if not self.title else 20
        return (self.rcParams['max_canvas_width_px'],
                self.rcParams['max_canvas_height_px'] + heighIncr)


    def compute_fig_size_cm(self):
        """
        ny, nx = self.n_sub_figs
        if not self.istransposed:
            x = min(self.rcParams['figure_width_cm']*nx,
                    self.rcParams['max_canvas_width_cm'])
            y = min(self.rcParams['figure_height_cm']*ny,
                    self.rcParams['max_canvas_height_cm'])
        elif self.istransposed and nx == 1:
            # Extend to full canvas size if transposed and single column
            x = self.rcParams['max_canvas_width_cm']
            y = min(self.rcParams['figure_height_cm']*ny,
                    self.rcParams['max_canvas_height_cm'])
        return x, y
        """
        heighIncr = 0 if not self.title else 0.5
        return (self.rcParams['max_canvas_width_cm'],
                self.rcParams['max_canvas_height_cm'] + heighIncr)


    def transpose(self):
        if not self.istransposed:
            self.istransposed = True
        else:
            self.istransposed = False


    def header(self, ext):
        if ext == ".svg":
            font = "fname '{}'".format(rcParams['svg_font'])
            return "set terminal svg enhanced size {}, {} {}" + font + "\nset output '{}.svg'\n"
        if ext == ".png":
            # font = "fname '{}'".format(rcParams['svg_font'])
            return "set terminal png enhanced size {}, {} {}" + "\nset output '{}.png'\n"
        if ext == ".eps":
            # return "set terminal epslatex color size {}cm, 5.75cm \nset out '{}.eps'\n"
            return "set terminal epslatex size {}cm, {}cm {}\nset out '{}_eps.eps'\n"

    def text(self, svg=False):
        data = self.data
        n_sub_figs = self.n_sub_figs
        body = ""

        def lt(arg):
            return ("lp" if arg == "line" else "p")


        if self.title:
            # increase top margin to fit a title
            self.rcParams["canvas_tmargin"] = str(
                    float(self.rcParams["canvas_tmargin"]) - 0.05)

        margins = ",".join([self.rcParams["canvas_" + _ + "margin"]
                            for _ in 'lrtb'])

        title_str = "" if not self.title else ' title "{}" '.format(self.title)
        body += ("set multiplot layout {}, {} {} margins screen {} spacing {}\n"
            .format(
                n_sub_figs[0], n_sub_figs[1],
                title_str,
                margins, self.rcParams['spacing'])
            )

        # write set style header
        if self.set_style:
            for elem in self.set_style:
                body += "set style {}\n".format(elem)

        body += ("set border {} lw {}\n"
            .format(
                self.rcParams['border'],
                self.rcParams['lw']
            ))

        data_blocks, invalids = self.str_inline_data_blocks(data)
        body += data_blocks

        for pid, d in data.items():
            pid = pid.replace("(", "").replace(")", "")

            body += ("\nset xrange [{:.4g}: {:.4g}]\n"
                        .format(d.xrange[0], d.xrange[1]))
            body += ("\nset yrange [{:.4g}: {:.4g}]\n"
                        .format(d.yrange[0], d.yrange[1]))

            body += ("\nset y2range [{:.4g}: {:.4g}]\n"
                        .format(d.yrange[0], d.yrange[1]))

            body += d.pre_text(svg)
            body += "\nplot "

            data_blocks = [e.format(pid) for e in d.ftext()]
            s = ("".join(intersperse(", \\\n", data_blocks)))
            body += s

            body += d.post_text()

        body += "\nunset multiplot"
        return body

    def str_inline_data_blocks(self, data):
        """  write data directly into  gnuplot script and mark invalids"""
        # TODO Move to gnuplot figure
        invalids = {}
        ret = ""
        for pid, d in data.items():
            for i, vals in enumerate(zip(d.x, d.y, d.z)):
                try:
                    x = vals[0]
                    y = vals[1]
                    z = vals[2]
                    x_ = (x if isinstance(x, tuple) else x.values)
                    y_ = y.values
                    if not len(y_):
                        invalids[pid, i] = True
                        continue
                    pid = pid.replace("(", "").replace(")", "")
                    ret += "${}_{} << EOD\n".format(pid, i)
                    for j in range(len(y)):
                        if isinstance(z, type(None)) :
                            ret += "{} {}\n".format(x_[j], y_[j])
                        else:
                            ret += "{} {} {}\n".format(x_[j], y_[j], z.values[j])
                    ret += "EOD\n"
                except Exception as e:
                    print(e, z)
                    invalids[pid, i] = True
        return ret, invalids


    # def _repr_svg_(self):
    #     self.write_file()
    #     return open(self.filename + ".svg", 'r').read()

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


class PlotProperties():

    def __init__(self):
        from collections import defaultdict
        self.properties = defaultdict(dict)

    def insert(self, field, properties):
        self.properties[field].update(properties)
        return self

    def set(self, inserts):
        for k, d in inserts.items():
            self.insert(k, d)

    def select(self, field, prop, default=None):
        field = self.properties[field]
        if not field:
            return
        else:
            return field.get(prop, default)


class Props():
    # TODO default args

    def __init__(self, name="None",
                 plot_properties=None,
                 symb=None, show_func=None):
        self.name = name
        self.plot_properties = plot_properties if plot_properties else PlotProperties()
        self.symb = symb
        self.show_func = show_func


def draw(x, y, data, title=None, func="line",
        z=None, figure=None, legend_prefix="", titles=None,
        names=None, **kwargs):
    """ draws a figure from x and y label and a dataframe
        if figure is given dataset will be drawn into existing figure
    """
    pP = kwargs.get('properties', Props())

    figure = figure if figure else GnuplotFigure(filename=kwargs.get("filename", None))
    y = (y if isinstance(y, list) else [y])
    for yi in y:
        x_data, y_data = data[x], data[yi]
        z = data[z] if z else z

        # First check explicitly specified name
        name = kwargs.get("name", None)

        # If no name given but properties
        if (not name and pP):
            name = yi if pP.name == "None" else pP.name

        else:
            name = "None"

        figure.add(
                x=x_data, y=y_data, z=z,
                legend=legend_prefix + name,
                lt=func)

    # # set axis ranges and labels
    for ax, data_set in {'x': x, 'y': y[0]}.items():
        label = _label(ax, data_set, pP)
        if label:
            l = getattr(figure, ax+'_label')
            setattr(l, "name", label)
            l = getattr(figure, ax+'2_label')
            setattr(l, "name", label)
        range_ = _range(ax, data_set, pP)
        if range_:
            setattr(figure, ax+'_range', range_)
            setattr(figure, ax+'2_range', range_)
        # if _log(ax, data_set):
        #     r = setattr(figure, ax+'_log', _log(ax, data_set))
    return figure


def _range(axis, field, properties, **kwargs):
    # Explicit Range
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

def _label(axis, field, properties, **kwargs):
    # Explicit Label
    axis_label = (axis + '_label').replace("2", "")
    label = kwargs.get(axis_label, False)
    if label:
        properties.plot_properties.insert(
            field, {axis_label: label})
    else:
        label = properties.plot_properties.select(
            field, axis_label, "None")
    return label
