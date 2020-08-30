from ExplorIA.src.interactive_selection import InteractiveSelection
import numpy as np
from bokeh.plotting import figure
from bokeh import palettes
from bokeh.models import ColumnDataSource

def fun_plot_sel(data):
    source = ColumnDataSource(data=dict(x=data[:, 0], y=data[:, 1], color=np.tile('#53777a', len(data))))
    TOOLS = "crosshair,pan,wheel_zoom,box_zoom,reset,box_select,lasso_select"
    f = figure(tools=TOOLS, plot_width=750, plot_height=750, background_fill_color="#fafafa",
               title="Selection des données")
    f.circle('x', 'y', source=source, size=5, color="color", alpha=0.8)
    return f, source

def fun_plot_res(data, sel_index):
    f = figure(plot_width=750, plot_height=750, background_fill_color="#fafafa",
               title="Résultat")
    sources = []
    for k, val in sel_index.items():
        sources.append(ColumnDataSource(data=dict(x=data[val, 0], y=data[val, 1])))
        f.circle('x', 'y', source=sources[-1], size=5, color=palettes.all_palettes["Category10"][np.mod(k, 10)], alpha=0.8)
    return f, sources

def fun_close(selection):
    print(selection)

if __name__ == '__main__':
    data = np.random.normal(0, 1, (100,2))

    int_sel = InteractiveSelection(data, fun_plot_sel, fun_plot_res, fun_close)