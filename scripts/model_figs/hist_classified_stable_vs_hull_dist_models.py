"""Histogram of the energy difference (either according to DFT ground truth [default] or
model predicted energy) to the convex hull for materials in the WBM data set. The
histogram stacks true/false positives/negatives with different colors.
"""


# %%
import math
from typing import Final

from pymatviz.io import save_fig

from matbench_discovery import PDF_FIGS, SITE_FIGS, formula_col, today
from matbench_discovery.plots import hist_classified_stable_vs_hull_dist, plt
from matbench_discovery.preds import (
    df_metrics,
    df_preds,
    e_form_col,
    each_pred_col,
    each_true_col,
)

__author__ = "Janosh Riebesell"
__date__ = "2022-12-01"


# %%
hover_cols = (df_preds.index.name, e_form_col, each_true_col, formula_col)
e_form_preds = "e_form_per_atom_pred"
facet_col = "Model"
# sort facet plots by model's F1 scores (optionally only show top n=6)
models = list(df_metrics.T.F1.sort_values().index)[::-1]

df_melt = df_preds.melt(
    id_vars=hover_cols,
    value_vars=models,
    var_name=facet_col,
    value_name=e_form_preds,
)

df_melt[each_pred_col] = (
    df_melt[each_true_col] + df_melt[e_form_preds] - df_melt[e_form_col]
)


# %%
backend: Final = "plotly"
n_cols = 2
n_rows = math.ceil(len(models) / n_cols)
# 'true' or 'pred': whether to put DFT or model-predicted hull distances on the x-axis
which_energy: Final = "pred"
kwds = (
    dict(
        facet_col=facet_col, facet_col_wrap=n_cols, category_orders={facet_col: models}
    )
    if backend == "plotly"
    else dict(by=facet_col, figsize=(20, 20), layout=(n_rows, n_cols), bins=500)
)

fig = hist_classified_stable_vs_hull_dist(
    df=df_melt,
    each_true_col=each_true_col,
    each_pred_col=each_pred_col,
    which_energy=which_energy,
    backend=backend,
    rolling_acc=None,
    stability_threshold=None,
    **kwds,  # type: ignore[arg-type]
)

# TODO add line showing the true hull distance histogram on each subplot
show_metrics = False
if backend == "matplotlib":
    fig = plt.gcf()
    fig.suptitle(f"{today} {which_energy=}", y=1.04, fontsize=18, fontweight="bold")
    plt.figlegend(
        *plt.gca().get_legend_handles_labels(),
        ncol=4,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.03),
        frameon=False,
    )
    # add metrics to subplot titles
    for ax in fig.axes:
        model_name = ax.get_title()
        assert model_name in models
        if not show_metrics:
            continue
        F1, FPR, FNR, DAF = (
            df_metrics[model_name][x] for x in "F1 FPR FNR DAF".split()
        )
        ax.set(title=f"{model_name} · {F1=:.2f} · {FPR=:.2f} · {FNR=:.2f} · {DAF=:.2f}")
else:
    for anno in fig.layout.annotations:
        model_name = anno.text = anno.text.split("=", 1).pop()
        if model_name not in models or not show_metrics:
            continue
        F1, FPR, FNR, DAF = (
            df_metrics[model_name][x] for x in "F1 FPR FNR DAF".split()
        )
        anno.text = f"{model_name} · {F1=:.2f} · {FPR=:.2f} · {FNR=:.2f} · {DAF=:.2f}"

    # fig.layout.height = 1000
    fig.layout.margin.update(t=50, b=30, l=30, r=0)
    fig.layout.legend.update(
        y=1.15, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)", orientation="h"
    )
    fig.update_yaxes(range=[0, 11_000], title_text=None)

    # for trace in fig.data:
    #     # no need to store all 250k x values in plot, leads to 1.7 MB file,
    #     # subsample every 10th point is enough to see the distribution
    #     trace.x = trace.x[::10]

    # increase height of figure
    fig.show()

img_name = f"hist-clf-{which_energy}-hull-dist-models-{n_rows}x{n_cols}"


# %%
orig_height = fig.layout.height
fig.layout.height = n_rows * 180
save_fig(fig, f"{SITE_FIGS}/{img_name}.svelte")
fig.layout.height = orig_height
save_fig(fig, f"{PDF_FIGS}/{img_name}.pdf", width=n_cols * 280, height=n_rows * 130)
