from bokeh.plotting import figure
from bokeh.models import Button
from bokeh.layouts import column, row, gridplot, Spacer
import time


class InteractiveSelection:

    def __init__(self, data, nrows, ncols, fun_close, fun_init_plot, fun_update_sel, fun_compute, nb_fig,
                 extra_args_fun_close=None, extra_args_fun_init_plot=None, extra_args_fun_update_sel=None,
                 extra_args_fun_compute=None, port=0):
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
        print(len(data))
        self.time_callback = time.time()
        self.nb_fig = nb_fig
        self.nrows = nrows
        self.ncols = ncols
        self.data = data
        self.fun_init_plot = fun_init_plot
        self.fun_compute = fun_compute
        self.fun_update_sel = fun_update_sel
        self.fun_close = fun_close
        self.extra_args_fun_init_plot = extra_args_fun_init_plot
        self.extra_args_fun_compute = extra_args_fun_compute
        self.extra_args_fun_update_sel = extra_args_fun_update_sel
        self.extra_args_fun_close = extra_args_fun_close
        self.ind_selected = {}  # Index des differentes selections de données
        self.current_group = 0

        self.source_sel = None
        self.source_res = []
        self.user_data = []
        self.figs = [figure()] * (nb_fig)
        # Les callback et callbacks
        # Ok
        self.ok_butt = Button(label="Ok", button_type="success")
        self.ok_butt.on_click(self.close)
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
        # Calculer
        self.calc_butt = Button(label="Calculer", button_type="success")
        self.calc_butt.on_click(self.comput_other_fig)
        # Refresh other figs
        self.refresh_butt = Button(label="Refresh", button_type="success")
        self.refresh_butt.on_click(self.refresh_plot)
        # Creating server
        from bokeh.server.server import Server
        server = Server({'/': self.bokeh_app}, num_procs=1, port=port)
        server.start()
        print('Opening Bokeh application on http://localhost:'+str(port))
        server.io_loop.add_callback(server.show, "/")
        server.io_loop.start()

    def bokeh_app(self, doc):
        # Générer les plots
        gridplot_child = []
        for nc in range(self.ncols):
            gridplot_child_row = []
            for nr in range(self.nrows):
                if nc * self.ncols + nr >= self.nb_fig:
                    gridplot_child_row.append(None)
                    break
                if nr == 0 and nc == 0:
                    TOOLS = "crosshair,pan,wheel_zoom,box_zoom,reset,box_select,lasso_select"
                    self.figs[nc * self.ncols + nr] = figure(tools=TOOLS, background_fill_color="#fafafa",
                                                             title="Selection des données")
                else:
                    TOOLS = "crosshair,pan,wheel_zoom,box_zoom,reset,box_select,lasso_select"
                    self.figs[nc * self.ncols + nr] = figure(tools=TOOLS, background_fill_color="#fafafa")
                gridplot_child_row.append(self.figs[nc * self.ncols + nr])
            gridplot_child.append(gridplot_child_row)
        if self.ncols == 1:
            grid = column(*gridplot_child, sizing_mode="stretch_both")
        elif self.nrows == 1:
            grid = row(*gridplot_child, sizing_mode="stretch_both")
        else:
            grid = gridplot(gridplot_child, sizing_mode="stretch_both")

        # Plotting selection plot
        if self.extra_args_fun_init_plot is not None:
            self.source_sel, self.source_res = self.fun_init_plot(self, *self.extra_args_fun_init_plot)
        else:
            self.source_sel, self.source_res = self.fun_init_plot(self)
        self.source_sel.selected.on_change('indices', self.update_sel)
        for s in self.source_res:
            if isinstance(s, list):
                s = s[0]
            s.selected.on_change('indices', self.update_sel)
        prec_next_row = row(self.prec_butt, self.next_butt, sizing_mode="stretch_width")
        refresh_calc_row = row(self.refresh_butt, self.calc_butt, sizing_mode="stretch_width")
        button_pan = column(self.del_butt, prec_next_row, refresh_calc_row, self.ok_butt)
        self.layout = column(grid, row(Spacer(), button_pan, Spacer(), sizing_mode="stretch_width"),
                             sizing_mode="stretch_width")
        doc.add_root(self.layout)

    def comput_other_fig(self):
        if self.extra_args_fun_compute is not None:
            self.fun_compute(self.data, self.ind_selected, self.figs, self.source_sel, self.source_res, self.user_data,
                             *self.extra_args_fun_compute)
        else:
            self.fun_compute(self.data, self.ind_selected, self.figs, self.source_sel, self.source_res, self.user_data)

    def refresh_plot(self):
        if self.extra_args_fun_update_sel is not None:
            self.fun_update_sel(self, *self.extra_args_fun_update_sel)
        else:
            self.fun_update_sel(self)

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
        self.source_sel.selected.indices = list(self.ind_selected[self.current_group])
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
        self.source_sel.selected.indices = list(self.ind_selected[self.current_group])
        self.prec_butt.disabled = False

    def update_sel(self, attr, old, new):
        self.ind_selected[self.current_group] = new

    # def refresh_plot(self):
    #     if self.extra_args_fun_update_sel is not None:
    #         self.fun_update_sel(self.data, self.ind_selected, self.source_sel, self.source_res,
    #                             *self.extra_args_fun_update_sel)
    #     else:
    #         self.fun_update_sel(self.data, self.ind_selected, self.source_sel, self.source_res)
    #     for s in self.source_res:
    #         if isinstance(s, list):
    #             s = s[0]
    #         s.selected.indices = self.ind_selected[self.current_group]

    def close(self):
        if self.extra_args_fun_close is not None:
            self.fun_close(self.data, self.ind_selected, self.source_sel, self.source_res, self.user_data,
                           *self.extra_args_fun_close)
        else:
            self.fun_close(self.data, self.ind_selected, self.source_sel, self.source_res, self.user_data)