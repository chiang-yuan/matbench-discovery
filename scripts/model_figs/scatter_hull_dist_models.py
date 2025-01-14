"""Scatter plot of actual vs predicted e_above_hull and e_form_per_atom for all
models. First 2 plots put all models in single figure with selectable traces.
Last plot is split into 2x3 subplots, one for each model.
"""


# %%
import math

import numpy as np
import plotly.express as px
from pymatviz.io import save_fig
from pymatviz.utils import add_identity_line, bin_df_cols

from matbench_discovery import PDF_FIGS, SITE_FIGS, formula_col
from matbench_discovery.plots import clf_colors
from matbench_discovery.preds import (
    df_metrics,
    df_preds,
    e_form_col,
    each_pred_col,
    each_true_col,
)

__author__ = "Janosh Riebesell"
__date__ = "2022-11-28"

e_form_pred_col = "e_form_per_atom_pred"
legend = dict(x=1, y=0, xanchor="right", yanchor="bottom", title=None)


# %%
facet_col = "Model"
hover_cols = (each_true_col, formula_col)
models = list(df_metrics.T.MAE.nsmallest(6).index)  # top 6 models by MAE
models = list(df_metrics)  # all models

df_melt = df_preds.melt(
    id_vars=(df_preds.index.name, e_form_col, *hover_cols),
    var_name=facet_col,
    value_vars=models,
    value_name=e_form_pred_col,
)

df_melt[each_pred_col] = (
    df_melt[each_true_col] + df_melt[e_form_pred_col] - df_melt[e_form_col]
)
df_bin = bin_df_cols(
    df_melt,
    bin_by_cols=[each_true_col, each_pred_col],
    group_by_cols=[facet_col],
    n_bins=200,
    bin_counts_col=(bin_cnt_col := "bin counts"),
)
df_bin = df_bin.reset_index()

# sort legend and facet plots by MAE
legend_order = list(df_metrics.T.MAE.sort_values().index)


# determine each point's classification to color them by
# now unused, can be used to color points by TP/FP/TN/FN
# true_pos, false_neg, false_pos, true_neg = classify_stable(
#     df_bin[each_true_col], df_bin[each_pred_col]
# )
# clf_col = "classified"
# df_bin[clf_col] = np.array(clf_labels)[
#     true_pos * 0 + false_neg * 1 + false_pos * 2 + true_neg * 3
# ]


# %% scatter plot of actual vs predicted e_form_per_atom
fig = px.scatter(
    df_bin,
    x=e_form_col,
    y=e_form_pred_col,
    color=facet_col,
    hover_data=hover_cols,
    hover_name=df_preds.index.name,
    opacity=0.7,
    category_orders={facet_col: legend_order},
)

for trace in fig.data:
    # initially hide all traces, let users select which models to compare
    trace.visible = "legendonly"
    model = trace.name
    assert model in df_preds, f"Unexpected {model=} not in {models}"
    MAE, R2 = df_metrics[model][["MAE", "R2"]]
    trace.name = f"{model} · {MAE=:.2f} · R<sup>2</sup>={R2:.2f}"

fig.update_layout(legend=legend)
add_identity_line(fig)
fig.show()

img_name = f"{SITE_FIGS}/e-form-scatter-models"
# save_fig(fig, f"{img_path}.svelte")


# %% scatter plot of actual vs predicted e_above_hull
fig = px.scatter(
    df_bin,
    x=each_true_col,
    y=each_pred_col,
    color=facet_col,
    hover_data=hover_cols,
    hover_name=df_preds.index.name,
    opacity=0.7,
    category_orders={facet_col: legend_order},
)

for trace in fig.data:
    trace.visible = "legendonly"
    model = trace.name
    assert model in df_preds, f"Unexpected {model=} not in {models}"
    MAE, R2 = df_metrics[model][["MAE", "R2"]]
    trace.name = f"{model} · {MAE=:.2f} · R<sup>2</sup>={R2:.2f}"

fig.update_layout(legend=legend)
add_identity_line(fig)
fig.show()

img_name = f"{SITE_FIGS}/e-above-hull-scatter-models"
# save_fig(fig, f"{img_path}.svelte")


# %% scatter plot of DFT vs predicted hull distance with each model in separate subplot
log_bin_cnt_col = f"log {bin_cnt_col}"
df_bin[log_bin_cnt_col] = np.log1p(df_bin[bin_cnt_col]).round(2)

n_cols = 2
n_rows = math.ceil(len(models) / n_cols)

fig = px.scatter(
    df_bin,
    x=each_true_col,
    y=each_pred_col,
    facet_col=facet_col,
    facet_col_wrap=n_cols,
    color=log_bin_cnt_col,
    facet_col_spacing=0.02,
    facet_row_spacing=0.04,
    hover_data=hover_cols,
    hover_name=df_preds.index.name,
    # color=clf_col,
    # color_discrete_map=clf_color_map,
    # opacity=0.4,
    range_x=(domain := (-4, 7)),
    range_y=domain,
    category_orders={facet_col: legend_order},
    # pick from https://plotly.com/python/builtin-colorscales
    color_continuous_scale="agsunset",
)

# manually set colorbar ticks and labels (needed after log1p transform)
tick_vals = [1, 10, 100, 1000, 10_000]
fig.layout.coloraxis.colorbar.update(
    tickvals=np.log1p(tick_vals), ticktext=list(map(str, tick_vals))
)

x_title = fig.layout.xaxis.title.text  # used in annotations below
y_title = fig.layout.yaxis.title.text

# iterate over subplots and set new title
for idx, anno in enumerate(fig.layout.annotations, 1):
    traces = [t for t in fig.data if t.xaxis == f"x{idx if idx > 1 else ''}"]
    # assert len(traces) in (0, 4), f"Plots must have 0 or 4 traces, got {len(traces)=}"

    model = anno.text.split("=", 1)[1]
    assert model in df_preds, f"Unexpected {model=} not in {list(df_preds)=}"
    # add MAE and R2 to subplot titles
    MAE, R2 = df_metrics[model][["MAE", "R2"]]
    fig.layout.annotations[
        idx - 1
    ].text = f"{model} · {MAE=:.2f} · R<sup>2</sup>={R2:.2f}"

    # remove subplot x and y axis titles
    fig.layout[f"xaxis{idx}"].title.text = ""
    fig.layout[f"yaxis{idx}"].title.text = ""

# add transparent rectangle with TN, TP, FN, FP labels in each quadrant
for sign_x, sign_y, color, label in zip(
    [-1, -1, 1, 1], [-1, 1, -1, 1], clf_colors, ("TP", "FN", "FP", "TN")
):
    # instead of coloring points in each quadrant, we can add a transparent
    # background to each quadrant (looks worse maybe than coloring points)
    # fig.add_shape(
    #     type="rect",
    #     x0=0,
    #     y0=0,
    #     x1=sign_x * 100,
    #     y1=sign_y * 100,
    #     fillcolor=color,
    #     opacity=0.2,
    #     layer="below",
    #     row="all",
    #     col="all",
    # )
    fig.add_annotation(
        x=(domain[0] if sign_x < 0 else domain[1]),
        y=(domain[0] if sign_y < 0 else domain[1]),
        xshift=-20 * sign_x,
        yshift=-20 * sign_y,
        text=label,
        showarrow=False,
        font=dict(size=16, color=color),
        row="all",
        col="all",
    )

# add dashed quadrant separators
fig.add_vline(x=0, line=dict(width=0.5, dash="dash"))
fig.add_hline(y=0, line=dict(width=0.5, dash="dash"))

fig.update_xaxes(nticks=5)
fig.update_yaxes(nticks=5)

# remove legend title and place legend centered above subplots, increase marker size
fig.layout.legend.update(
    title="", orientation="h", x=0.5, xanchor="center", y=1.15, itemsizing="constant"
)

# fig.update_layout(yaxis=dict(scaleanchor="x", scaleratio=1))

axis_titles = dict(xref="paper", yref="paper", showarrow=False)
fig.add_annotation(  # x-axis title
    x=0.5,
    y=-0.06,
    text=x_title,
    **axis_titles,
)
fig.add_annotation(  # y-axis title
    x=-0.07,
    y=0.5,
    text=y_title,
    textangle=-90,
    **axis_titles,
)
fig.layout.height = 230 * n_rows
fig.layout.coloraxis.colorbar.update(orientation="h", thickness=9, len=0.5, y=1.05)
# fig.layout.width = 1100
fig.layout.margin.update(l=40, r=10, t=30, b=60)
fig.update_xaxes(matches=None)
fig.update_yaxes(matches=None)
fig.show()


# %%
fig_name = f"each-scatter-models-{n_rows}x{n_cols}"
save_fig(fig, f"{SITE_FIGS}/{fig_name}.svelte")
save_fig(fig, f"{PDF_FIGS}/{fig_name}.pdf")
