from ExplorIA.src.interactive_selection import InteractiveSelection
import numpy as np, glob
from bokeh.plotting import figure
from bokeh import palettes
from bokeh.models import ColumnDataSource
from mppv_GY_SUNR import ROOT_DIR as root_mppv_gy_sunr
import pyarrow.parquet as pq, pandas as pd, numpy as np
import pyarrow as pa
from sklearn.semi_supervised import LabelPropagation, LabelSpreading
from sklearn.preprocessing import StandardScaler
from factoria.modules.data_modeling.ModelingV1 import ModelingV1


def fun_init_plot(data, figs):
    figs[1].title.text = "Selection vs temps"
    source_sel = ColumnDataSource(data=dict(x=data[:, 0], y=data[:, 1], color=np.tile('#53777a', len(data))))
    figs[0].circle('x', 'y', source=source_sel, size=3, color="color", alpha=0.5)

    sources = []
    colors = np.array(['#53777a'] * len(data), dtype=object)

    # plot des résultats de la selection vs time
    source = ColumnDataSource(data=dict(x=time, y=data[:, 0], color=colors))
    figs[1].circle('x', 'y', color="color", source=source, size=3, alpha=1)
    sources.append(source)
    return source_sel, sources


def fun_update_sel(data, ind_selected, sources_sel, source_res):
    colors = np.array(['#53777a'] * len(data), dtype=object)
    for k, val in ind_selected.items():
        colors[val] = palettes.all_palettes["Category10"][10][np.mod(k, 10)]
    sources_sel.data["color"] = colors
    for s in source_res:
        s.data["color"] = colors


def fun_compute(data, ind_selected, figs, _, sources_res, all_data):
    if not isinstance(sources_res, list):
        sources_res = [sources_res]
    input_gam = ['PV Power (kW)', 'PV Voltage (V)', 'Frequency (Hz)', 'Cos Phi', 'Irrad_Horiz (W/m2)', 'Temp_Amb (C)']
    output_gam = all_data['Output Apparent Power (kVA)'] / all_data['PV Power (kW)']
    for k, val in ind_selected.items():
        dmV1 = ModelingV1(all_data.loc[all_data.index[val], input_gam], output_gam.iloc[val],
                      spline_search_space=np.arange(5, 51, 5),
                      lam_search_space=np.logspace(-3, 5, 20))
        dmV1.perform(verbose=True, scoring='GCV')
        # gam = dmV1.gam
        yhat = dmV1.yhat

        if len(sources_res) >= k:
            sources_res[k] = ColumnDataSource(data=dict(x=all_data.index, y=yhat*data[val, 1], color="#FFD700"))
        else:
            sources_res[k].data=dict(x=all_data.index, y=yhat*data[val, 1], color="#FFD700")
        figs[1].line("x", "y", color="color", source=sources_res[k], line_width=2)

def fun_close(selection):
    print(selection)


if __name__ == '__main__':
    weather_path = root_mppv_gy_sunr + "/data/weather_cleaned.parquet"
    weather_data = pa.Table.to_pandas(pq.read_table(weather_path))
    # Pour tous les onduleurs
    for ond_file in glob.glob(root_mppv_gy_sunr + "/data/data_inv_GY/*.parquet"):
        if "AMBATOLAMPY" in ond_file:
            continue
        data = pq.read_table(ond_file).to_pandas()
        # removing zero production
        data = data.loc[~((data['PV Power (kW)'] <= 10 ** -1) | (data['Output Apparent Power (kVA)'] <= 10 ** -1) | (
                data['P Output (kW)'] <= 10 ** -1))]
        data.drop(columns=["chunk_inv"], inplace=True)
        data.dropna(how="all", axis=0, inplace=True)
        ptr = ond_file.split('\\')[-1].split("_")[2]
        cent = ond_file.split('\\')[-1].split("_")[1]
        weather_data_tp = weather_data.loc[weather_data["Centrale"] == cent]
        weather_data_tp = weather_data_tp.loc[weather_data_tp["PTR"] == weather_data_tp["PTR"].unique()[0]]
        weather_data_tp = weather_data_tp.loc[data.index]
        ind_na = data[['PV Power (kW)', 'PV Voltage (V)', 'Frequency (Hz)', 'Cos Phi', 'Output Apparent Power (kVA)']].isna().any(axis=1) | \
                 weather_data_tp[['Irrad_Horiz (W/m2)', 'Temp_Amb (C)']].isna().any(axis=1)

        data = pd.concat([data, weather_data_tp], axis=1)
        data = data.loc[~ind_na]
        index = (data.index >= pd.to_datetime("2019-04-01")) & (data.index <= pd.to_datetime("2019-10-01"))
        data_sample = data.loc[index].sort_index()
        p_out = data_sample['Output Apparent Power (kVA)'].values
        p_in = data_sample['PV Power (kW)'].values
        time = data_sample.index

        # from sklearn.cluster import DBSCAN
        # import matplotlib.pyplot as plt
        # ind_large_pord = (p_out>800) & (p_out/p_in > 0.96)
        # db = DBSCAN(n_jobs=-1)
        # cls = db.fit_predict(np.vstack([p_in[ind_large_pord], p_out[ind_large_pord]/p_in[ind_large_pord], np.arange(len(time[ind_large_pord]))]).T)
        # plt.figure()
        # for c in np.unique(cls):
        #     plt.scatter(p_in[ind_large_pord][c == cls], p_out[ind_large_pord][c == cls]/p_in[ind_large_pord][c == cls], s=3)
        # plt.scatter(p_in, p_in/p_out, c='k', alpha=0.3, s=3)
        # plt.show(block=False)

        int_sel = InteractiveSelection(np.vstack([p_in, p_out/p_in]).T, 2, 1, fun_close, fun_init_plot, fun_update_sel,
                                       lambda data, sel_ind, figs, sources_sel, sources_res:
                                       fun_compute(data, sel_ind, figs, sources_sel, sources_res, data_sample), 2)