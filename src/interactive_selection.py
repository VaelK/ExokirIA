from bokeh.plotting import figure, output_file, show, Figure, curdoc
from bokeh.models import Button, CustomJS
from bokeh.layouts import column, row, gridplot, Spacer

class InteractiveSelection:

    def __init__(self, data, nrows, ncols, fun_close, fun_plot_sel, fun_plot_res):
        """
        :param data: np.ndarray
            data that are ploted
        :param nrows: int
            Number of rows in the grid of plots
        :param ncols: int
            Number of columns in the grid of plots
        :param fun_close: function
            Function that close the app
        :param args:
            List of function that are called to generate each plots. Plots are displayed from laft to right and top to
            bottom in the grid plot
        """
        self.nrows=nrows
        self.ncols=ncols
        self.data = data
        self.fun_plot_sel = fun_plot_sel
        self.fun_plots = fun_plot_res
        self.fun_close = fun_close
        self.ind_selected = {}  # Index des differentes selections de données
        self.current_group = 0

        self.source_sel = None
        self.source_res = []
        self.figs = [figure()]*(nrows*ncols)
        # Les callback et callbacks
        # Ok
        self.ok_butt = Button(label="Ok", button_type="success")
        self.ok_butt.on_click(lambda: self.fun_close(self.ind_selected))
        # Supprimer
        self.del_butt = Button(label="Supprimer", button_type="success")
        self.del_butt.on_click(self.callback_del)
        # Prédent
        self.prec_butt = Button(label="Groupe précédent", button_type="success")
        self.prec_butt.on_click(self.callback_previous)
        self.prec_butt.disabled = True
        # Suivant
        self.next_butt = Button(label="Groupe suivant", button_type="success")
        self.next_butt.on_click(self.callback_next)
        #Calculer
        self.calc_butt = Button(label="Calculer", button_type="success")
        self.calc_butt.on_click(self.comput_other_fig)

        # Creating server
        from bokeh.server.server import Server
        server = Server({'/': self.bokeh_app}, num_procs=1)
        server.start()
        print('Opening Bokeh application on http://localhost')
        server.io_loop.add_callback(server.show, "/")
        server.io_loop.start()

    def bokeh_app(self, doc):
        # Générer les plots
        gridplot_child = []
        for nc in range(self.ncols):
            gridplot_child_row = []
            for nr in range(self.nrows):
                if nr == 0 and nc == 0:
                    TOOLS = "crosshair,pan,wheel_zoom,box_zoom,reset,box_select,lasso_select"
                    f = figure(tools=TOOLS, background_fill_color="#fafafa",
                               title="Selection des données")
                    self.figs[0], self.source_sel = self.fun_plot_sel(self.data, f)
                    assert isinstance(self.figs[0], Figure)
                    self.plot_width = self.figs[0].plot_width
                    self.plot_height = self.figs[0].plot_height
                else:
                    self.figs[nc*self.ncols+nr] = figure(plot_width=self.plot_width, plot_height=self.plot_height)
                gridplot_child_row.append(self.figs[nc*self.ncols+nr])
            gridplot_child.append(gridplot_child_row)
        grid = gridplot(gridplot_child, sizing_mode="stretch_both")
        self.source_sel.selected.on_change('indices', self.update_sel)

        prec_next_row = row(self.prec_butt, self.next_butt, sizing_mode="stretch_width")
        button_pan = column(self.del_butt, prec_next_row, self.calc_butt, self.ok_butt)
        self.layout = column(grid, row(Spacer(), button_pan, Spacer(), sizing_mode="stretch_width"),
                             sizing_mode="stretch_width")
        doc.add_root(self.layout)

    def comput_other_fig(self):
        for s in self.source_res:
            if isinstance(s, list):
                for sub_s in s:
                    for k, v in sub_s.data.items():
                        sub_s.data[k] = []
            else:
                for k, v in s.data.items():
                    s.data[k] = []
        self.figs[1:], self.source_res = self.fun_plots(self.data, self.ind_selected, self.figs[1:])
        # for nc in range(self.ncols):
        #     for nr in range(self.nrows):
        #         if nr == 0 and nc == 0:
        #             fig = self.layout.children[0].children[1].children[nc*self.ncols + nr][0]
        #         else:
        #             assert isinstance(figs[nc * self.ncols + nr - 1], Figure)
        #             fig = figs[nc * self.ncols + nr - 1]
        #         fig.plot_width = self.plot_width
        #         fig.plot_height = self.plot_height
        #         self.layout.children[0].children[1].children[nc*self.ncols + nr] = (fig, nc, nr)

    def callback_del(self):
        """
        To del a group from data selection
        :return:
        """
        pass

    def callback_previous(self):
        """
        Show previous selection
        :return:
        """
        self.current_group = self.current_group - 1
        self.source_sel.selected.indices = self.ind_selected[self.current_group]
        if self.current_group == 0:
            self.prec_butt.disabled = True
        else:
            self.prec_butt.disabled = False

    def callback_next(self):
        """
        Show next selection
        :return:
        """
        self.current_group = self.current_group + 1
        if self.current_group not in self.ind_selected.keys():
            self.ind_selected[self.current_group] = []
        self.source_sel.selected.indices = self.ind_selected[self.current_group]
        self.prec_butt.disabled = False

    def update_sel(self, _, old, new):
        self.ind_selected[self.current_group] = new