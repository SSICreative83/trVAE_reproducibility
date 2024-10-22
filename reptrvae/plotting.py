import matplotlib
import numpy
import pandas as pd
import scanpy as sc
from adjustText import adjust_text
from matplotlib import pyplot
from scipy import stats, sparse

font = {'family': 'Arial',
        # 'weight' : 'bold',
        'size': 14}

matplotlib.rc('font', **font)
matplotlib.rc('ytick', labelsize=14)
matplotlib.rc('xtick', labelsize=14)


def reg_mean_plot(adata, condition_key, axis_keys, labels, path_to_save="./reg_mean.pdf", gene_list=None,
                  top_100_genes=None,
                  show=False,
                  legend=True, title=None,
                  x_coeff=0.30, y_coeff=0.8, fontsize=14, **kwargs):
    """
        Plots mean matching figure for a set of specific genes.

        # Parameters
            adata: `~anndata.AnnData`
                Annotated Data Matrix.
            condition_key: basestring
                Condition state to be used.
            axis_keys: dict
                dictionary of axes labels.
            path_to_save: basestring
                path to save the plot.
            gene_list: list
                list of gene names to be plotted.
            show: bool
                if `True`: will show to the plot after saving it.

        # Example
        ```python
        import anndata
        import scgen
        import scanpy as sc
        scripts = sc.read("./tests/data/scripts.h5ad", backup_url="https://goo.gl/33HtVh")
        network = scgen.VAEArith(x_dimension=scripts.shape[1], model_path="../models/test")
        network.scripts(train_data=scripts, n_epochs=0)
        unperturbed_data = scripts[((scripts.obs["cell_type"] == "CD4T") & (scripts.obs["condition"] == "control"))]
        condition = {"ctrl": "control", "stim": "stimulated"}
        pred, delta = network.predict(adata=scripts, adata_to_predict=unperturbed_data, conditions=condition)
        pred_adata = anndata.AnnData(pred, obs={"condition": ["pred"] * len(pred)}, var={"var_names": scripts.var_names})
        CD4T = scripts[scripts.obs["cell_type"] == "CD4T"]
        all_adata = CD4T.concatenate(pred_adata)
        scgen.plotting.reg_mean_plot(all_adata, condition_key="condition", axis_keys={"x": "control", "y": "pred", "y1": "stimulated"},
                                     gene_list=["ISG15", "CD3D"], path_to_save="tests/reg_mean.pdf", show=False)
        network.sess.close()
        ```

    """
    import seaborn as sns
    sns.set()
    sns.set(color_codes=True)
    if sparse.issparse(adata.X):
        adata.X = adata.X.A
    diff_genes = top_100_genes
    stim = adata[adata.obs[condition_key] == axis_keys["y"]]
    ctrl = adata[adata.obs[condition_key] == axis_keys["x"]]
    if diff_genes is not None:
        if hasattr(diff_genes, "tolist"):
            diff_genes = diff_genes.tolist()
        adata_diff = adata[:, diff_genes]
        stim_diff = adata_diff[adata_diff.obs[condition_key] == axis_keys["y"]]
        ctrl_diff = adata_diff[adata_diff.obs[condition_key] == axis_keys["x"]]
        x_diff = numpy.average(ctrl_diff.X, axis=0)
        y_diff = numpy.average(stim_diff.X, axis=0)
        m, b, r_value_diff, p_value_diff, std_err_diff = stats.linregress(x_diff, y_diff)
        print('reg_mean_top100:', r_value_diff ** 2)
    if "y1" in axis_keys.keys():
        real_stim = adata[adata.obs[condition_key] == axis_keys["y1"]]
    x = numpy.average(ctrl.X, axis=0)
    y = numpy.average(stim.X, axis=0)
    m, b, r_value, p_value, std_err = stats.linregress(x, y)
    print('reg_mean_all:', r_value ** 2)
    df = pd.DataFrame({axis_keys["x"]: x, axis_keys["y"]: y})
    ax = sns.regplot(x=axis_keys["x"], y=axis_keys["y"], data=df, scatter_kws={'rasterized': True})
    ax.tick_params(labelsize=fontsize)
    if "range" in kwargs:
        start, stop, step = kwargs.get("range")
        ax.set_xticks(numpy.arange(start, stop, step))
        ax.set_yticks(numpy.arange(start, stop, step))
    # _p1 = pyplot.scatter(x, y, marker=".", label=f"{axis_keys['x']}-{axis_keys['y']}")
    # pyplot.plot(x, m * x + b, "-", color="green")
    ax.set_xlabel(labels["x"], fontsize=fontsize)
    ax.set_ylabel(labels["y"], fontsize=fontsize)
    # if "y1" in axis_keys.keys():
    # y1 = numpy.average(real_stim.X, axis=0)
    # _p2 = pyplot.scatter(x, y1, marker="*", c="red", alpha=.5, label=f"{axis_keys['x']}-{axis_keys['y1']}")
    if gene_list is not None:
        texts = []
        for i in gene_list:
            j = adata.var_names.tolist().index(i)
            x_bar = x[j]
            y_bar = y[j]
            texts.append(pyplot.text(x_bar, y_bar, i, fontsize=11, color="black"))
            pyplot.plot(x_bar, y_bar, 'o', color="red", markersize=5)
            # if "y1" in axis_keys.keys():
            # y1_bar = y1[j]
            # pyplot.text(x_bar, y1_bar, i, fontsize=11, color="black")
    if gene_list is not None:
        adjust_text(texts, x=x, y=y, arrowprops=dict(arrowstyle="->", color='grey', lw=0.5), force_points=(0.0, 0.0))
    if legend:
        pyplot.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    if title is None:
        pyplot.title(f"", fontsize=fontsize)
    else:
        pyplot.title(title, fontsize=fontsize)
    ax.text(max(x) - max(x) * x_coeff, max(y) - y_coeff * max(y),
            r'$\mathrm{R^2_{\mathrm{\mathsf{all\ genes}}}}$= ' + f"{r_value ** 2:.2f}",
            fontsize=kwargs.get("textsize", fontsize))
    if diff_genes is not None:
        ax.text(max(x) - max(x) * x_coeff, max(y) - (y_coeff + 0.15) * max(y),
                r'$\mathrm{R^2_{\mathrm{\mathsf{top\ ' + str(
                    len(top_100_genes)) + '\ DEGs}}}}$= ' + f"{r_value_diff ** 2:.2f}",
                fontsize=kwargs.get("textsize", fontsize))
    pyplot.savefig(f"{path_to_save}", bbox_inches='tight', dpi=100)
    if show:
        pyplot.show()
    pyplot.close()


def reg_var_plot(adata, condition_key, axis_keys, labels, path_to_save="./reg_var.pdf", gene_list=None,
                 top_100_genes=None, show=False,
                 legend=True, title=None,
                 x_coeff=0.30, y_coeff=0.8, fontsize=14, **kwargs):
    """
        Plots variance matching figure for a set of specific genes.

        # Parameters
            adata: `~anndata.AnnData`
                Annotated Data Matrix.
            condition_key: basestring
                Condition state to be used.
            axis_keys: dict
                dictionary of axes labels.
            path_to_save: basestring
                path to save the plot.
            gene_list: list
                list of gene names to be plotted.
            show: bool
                if `True`: will show to the plot after saving it.

        # Example
        ```python
        import anndata
        import scgen
        import scanpy as sc
        scripts = sc.read("./tests/data/scripts.h5ad", backup_url="https://goo.gl/33HtVh")
        network = scgen.VAEArith(x_dimension=scripts.shape[1], model_path="../models/test")
        network.scripts(train_data=scripts, n_epochs=0)
        unperturbed_data = scripts[((scripts.obs["cell_type"] == "CD4T") & (scripts.obs["condition"] == "control"))]
        condition = {"ctrl": "control", "stim": "stimulated"}
        pred, delta = network.predict(adata=scripts, adata_to_predict=unperturbed_data, conditions=condition)
        pred_adata = anndata.AnnData(pred, obs={"condition": ["pred"] * len(pred)}, var={"var_names": scripts.var_names})
        CD4T = scripts[scripts.obs["cell_type"] == "CD4T"]
        all_adata = CD4T.concatenate(pred_adata)
        scgen.plotting.reg_var_plot(all_adata, condition_key="condition", axis_keys={"x": "control", "y": "pred", "y1": "stimulated"},
                                    gene_list=["ISG15", "CD3D"], path_to_save="tests/reg_var4.pdf", show=False)
        network.sess.close()
        ```

        """
    import seaborn as sns
    sns.set()
    sns.set(color_codes=True)
    if sparse.issparse(adata.X):
        adata.X = adata.X.A
    diff_genes = top_100_genes
    stim = adata[adata.obs[condition_key] == axis_keys["y"]]
    ctrl = adata[adata.obs[condition_key] == axis_keys["x"]]
    if diff_genes is not None:
        if hasattr(diff_genes, "tolist"):
            diff_genes = diff_genes.tolist()
        adata_diff = adata[:, diff_genes]
        stim_diff = adata_diff[adata_diff.obs[condition_key] == axis_keys["y"]]
        ctrl_diff = adata_diff[adata_diff.obs[condition_key] == axis_keys["x"]]
        x_diff = numpy.var(ctrl_diff.X, axis=0)
        y_diff = numpy.var(stim_diff.X, axis=0)
        m, b, r_value_diff, p_value_diff, std_err_diff = stats.linregress(x_diff, y_diff)
        print('reg_var_top100:', r_value_diff ** 2)
    if "y1" in axis_keys.keys():
        real_stim = adata[adata.obs[condition_key] == axis_keys["y1"]]
    x = numpy.var(ctrl.X, axis=0)
    y = numpy.var(stim.X, axis=0)
    m, b, r_value, p_value, std_err = stats.linregress(x, y)
    print('reg_var_all:', r_value ** 2)
    df = pd.DataFrame({axis_keys["x"]: x, axis_keys["y"]: y})
    ax = sns.regplot(x=axis_keys["x"], y=axis_keys["y"], data=df, scatter_kws={'rasterized': True})
    ax.tick_params(labelsize=fontsize)
    if "range" in kwargs:
        start, stop, step = kwargs.get("range")
        ax.set_xticks(numpy.arange(start, stop, step))
        ax.set_yticks(numpy.arange(start, stop, step))
    # _p1 = pyplot.scatter(x, y, marker=".", label=f"{axis_keys['x']}-{axis_keys['y']}")
    # pyplot.plot(x, m * x + b, "-", color="green")
    ax.set_xlabel(labels['x'], fontsize=fontsize)
    ax.set_ylabel(labels['y'], fontsize=fontsize)
    if "y1" in axis_keys.keys():
        y1 = numpy.var(real_stim.X, axis=0)
        _p2 = pyplot.scatter(x, y1, marker="*", c="grey", alpha=.5, label=f"{axis_keys['x']}-{axis_keys['y1']}")
    if gene_list is not None:
        for i in gene_list:
            j = adata.var_names.tolist().index(i)
            x_bar = x[j]
            y_bar = y[j]
            pyplot.text(x_bar, y_bar, i, fontsize=11, color="black")
            pyplot.plot(x_bar, y_bar, 'o', color="red", markersize=5)
            if "y1" in axis_keys.keys():
                y1_bar = y1[j]
                pyplot.text(x_bar, y1_bar, '*', color="black", alpha=.5)
    if legend:
        pyplot.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    if title is None:
        pyplot.title(f"", fontsize=12)
    else:
        pyplot.title(title, fontsize=12)
    ax.text(max(x) - max(x) * x_coeff, max(y) - y_coeff * max(y),
            r'$\mathrm{R^2_{\mathrm{\mathsf{all\ genes}}}}$= ' + f"{r_value ** 2:.2f}",
            fontsize=kwargs.get("textsize", fontsize))
    if diff_genes is not None:
        ax.text(max(x) - max(x) * x_coeff, max(y) - (y_coeff + 0.15) * max(y),
                r'$\mathrm{R^2_{\mathrm{\mathsf{top\ ' + str(
                    len(top_100_genes)) + '\ DEGs}}}}$= ' + f"{r_value_diff ** 2:.2f}",
                fontsize=kwargs.get("textsize", fontsize))
    pyplot.savefig(f"{path_to_save}", bbox_inches='tight', dpi=100)
    if show:
        pyplot.show()
    pyplot.close()


def plot_umap(adata, condition_key=None, cell_type_key=None, frameon=False, path_to_save=None, model_name="",
              ext='pdf', title=""):
    if cell_type_key is None and condition_key is None:
        raise Exception('at least one of cell_type_key or condition_key has to be set')

    last_figdir = sc.settings.figdir
    sc.settings.figdir = path_to_save
    sc.pp.neighbors(adata)
    sc.tl.umap(adata)

    if condition_key:
        sc.pl.umap(adata, color=condition_key, frameon=frameon, save=f"_{model_name}_condition.{ext}", title=title)
    if cell_type_key:
        sc.pl.umap(adata, color=cell_type_key, frameon=frameon, save=f"_{model_name}_cell_type.{ext}", title=title)

    sc.settings.figdir = last_figdir
