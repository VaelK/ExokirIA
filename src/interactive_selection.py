from bokeh.plotting import figure, output_file, show, Figure, curdoc
from bokeh.models import Button, CustomJS
from bokeh.layouts import column, row


class InteractiveSelection:

    def __init__(self, data, fun_plot_sel, fun_plot_res, fun_close):
        self.data = data
        self.fun_plot_sel = fun_plot_sel
        self.fun_plot_res = fun_plot_res
        self.fun_close = fun_close
        self.ind_selected = {}  # Index des differentes selections de données
        self.current_group = 0

        self.source_left = None
        self.source_right = None
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

        # Creating server
        from bokeh.server.server import Server
        server = Server({'/': self.bokeh_app}, num_procs=1)
        server.start()
        print('Opening Bokeh application on http://localhost:5006/')
        server.io_loop.add_callback(server.show, "/")
        server.io_loop.start()

    def bokeh_app(self, doc):
        # Générer les plots
        fig_left, self.source_left = self.fun_plot_sel(self.data)
        fig_right, self.source_right = self.fun_plot_res(self.data, self.ind_selected)
        self.source_left.selected.on_change('indices', self.update_sel)
        # cheking that output is figure
        assert isinstance(fig_left, Figure)
        assert isinstance(fig_right, Figure)
        # check that lasso_select and box_select are in tools

        plt_row = row(fig_left, fig_right)
        prec_ok_next_row = row(self.prec_butt, self.ok_butt, self.next_butt)
        butt_col = column(self.del_butt, prec_ok_next_row)
        layout = column(plt_row, butt_col)
        doc.add_root(layout)

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
        self.source_left.selected.indices = self.ind_selected[self.current_group]
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
        self.source_left.selected.indices = self.ind_selected[self.current_group]
        self.prec_butt.disabled = False

    def update_sel(self, _, old, new):
        self.ind_selected[self.current_group] = new