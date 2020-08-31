from ExplorIA.src.interactive_selection import InteractiveSelection
import numpy as np, glob
from bokeh.plotting import figure
from bokeh import palettes
from bokeh.models import ColumnDataSource
from mppv_GY_SUNR import ROOT_DIR as root_mppv_gy_sunr
import pyarrow.parquet as pq, pandas as pd, numpy as np
from sklearn.semi_supervised import LabelPropagation, LabelSpreading
from sklearn.preprocessing import StandardScaler


def fun_plot_sel(data, f):
    source = ColumnDataSource(data=dict(x=data[:, 0], y=data[:, 1], color=np.tile('#53777a', len(data))))
    f.circle('x', 'y', source=source, size=3, color="color", alpha=0.5)
    return f, source


def fun_plot_res(data, sel_index, figs, time):
    print(sel_index)
    for f in figs:
        f.background_fill_color="#fafafa"
    figs[0].title.text="Résultat clustering"
    figs[1].title.text="Selection vs temps"
    figs[2].title.text="Clustering vs temps"
    sources = []

    #traitement clustering
    label = np.tile(-1, len(data))
    for k, val in sel_index.items():
        label[val] = k
    lab_prop = LabelSpreading(kernel="knn", n_jobs=-1)
    training_data = StandardScaler().fit_transform(np.hstack([data, np.arange(len(data))[:, np.newaxis]]))
    training_data[:, 2] = training_data[:, 2]*10
    training_data = training_data[:, 2][:, np.newaxis] #On ne clusterise qu'avec le temps
    lab_prop.fit(training_data, label[:, np.newaxis])
    new_label = lab_prop.predict(training_data)

    # plot des résultats du clustering
    source = []
    for ilab, lab in enumerate(np.unique(new_label)):
        source.append(ColumnDataSource(data=dict(x=data[new_label == lab, 0], y=data[new_label == lab, 1])))
        if lab == -1:
            color = "black"
        else:
            color = palettes.all_palettes["Category10"][10][np.mod(ilab, 10)]
        figs[0].circle('x', 'y', source=source[-1], size=3, color=color, alpha=0.5)
    sources.append(source)

    # plot des résultats de la selection vs time
    source = []
    for k, val in sel_index.items():
        source.append(ColumnDataSource(data=dict(x=time[val], y=data[val, 0])))
        if k == -1:
            color = "black"
        else:
            color = palettes.all_palettes["Category10"][10][np.mod(k, 10)]
        figs[1].circle('x', 'y', source=source[-1], size=3, color=color, alpha=1)
    sources.append(source)

    # plot des résultats du clustering vs time
    source = []
    for ilab, lab in enumerate(np.unique(new_label)):
        source.append(ColumnDataSource(data=dict(x=time[new_label == lab], y=data[new_label == lab, 0])))
        if lab == -1:
            color = "black"
        else:
            color = palettes.all_palettes["Category10"][10][np.mod(ilab, 10)]
        figs[2].circle('x', 'y', source=source[-1], size=3, color=color, alpha=1)
    sources.append(source)
    return figs, sources

def fun_close(selection):
    print(selection)


if __name__ == '__main__':
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
        ind_na = data[['Cos Phi', 'Frequency (Hz)', 'Grid RMS Current Phase 1 (A)',
                       'Grid RMS Current Phase 2 (A)', 'Grid RMS Current Phase 3 (A)',
                       'Grid RMS Voltage Phase 1 (V)', 'Grid RMS Voltage Phase 2 (V)',
                       'Grid RMS Voltage Phase 3 (V)', 'Output Apparent Power (kVA)',
                       'P Output (kW)', 'PV Current (A)', 'PV Power (kW)', 'PV Voltage (V)',
                       'Q Output (kVAr)', 'eta_meas']].isna().any(axis=1)
        data = data.loc[~ind_na]

    index = (data.index >= pd.to_datetime("2019-04-01")) & (data.index <= pd.to_datetime("2019-10-01"))
    data_sample = data.loc[index].sort_index()
    p_out = data_sample['Output Apparent Power (kVA)'].values
    p_in = data_sample['PV Power (kW)'].values
    time = data_sample.index

    from sklearn.cluster import DBSCAN
    import matplotlib.pyplot as plt
    ind_large_pord = (p_out>800) & (p_out/p_in > 0.96)
    db = DBSCAN(n_jobs=-1)
    cls = db.fit_predict(np.vstack([p_in[ind_large_pord], p_out[ind_large_pord]/p_in[ind_large_pord], np.arange(len(time[ind_large_pord]))]).T)
    plt.figure()
    for c in np.unique(cls):
        plt.scatter(p_in[ind_large_pord][c == cls], p_out[ind_large_pord][c == cls]/p_in[ind_large_pord][c == cls], s=3)
    plt.scatter(p_in, p_in/p_out, c='k', alpha=0.3, s=3)
    plt.show(block=False)

    int_sel = InteractiveSelection(np.vstack([p_in, p_out/p_in]).T, 2, 2, fun_close, fun_plot_sel, lambda data, sel_ind, figs: fun_plot_res(data, sel_ind, figs, time))