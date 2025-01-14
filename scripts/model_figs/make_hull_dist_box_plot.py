# %%
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from pymatviz.io import save_fig

from matbench_discovery import PDF_FIGS, SITE_FIGS, plots
from matbench_discovery.preds import df_each_err, models

__author__ = "Janosh Riebesell"
__date__ = "2023-05-25"


# %%
ax = df_each_err[models].plot.box(
    showfliers=False,
    rot=90,
    figsize=(12, 6),
    # color="blue",
    # different fill colors for each box
    # patch_artist=True,
    # notch=True,
    # bootstrap=10000,
    showmeans=True,
    # meanline=True,
)
ax.axhline(0, linewidth=1, color="gray", linestyle="--")


# %%
ax = sns.violinplot(
    data=df_each_err[models], inner="quartile", linewidth=0.3, palette="Set2", width=1
)
ax.set(ylim=(-0.9, 0.9))

for idx, label in enumerate(ax.get_xticklabels()):
    label.set_va("bottom" if idx % 2 else "top")
    # lower all labels
    label.set_y(label.get_position()[1] - 0.05)


# %%
px.violin(
    df_each_err[models].melt(),
    x="variable",
    y="value",
    color="variable",
    violinmode="overlay",
    box=True,
    # points="all",
    hover_data={"variable": False},
    width=1000,
    height=500,
)


# %%
fig = go.Figure()
fig.layout.yaxis.title = plots.quantity_labels["e_above_hull_error"]
fig.layout.margin = dict(l=0, r=0, b=0, t=0)

for idx, model in enumerate(models):
    ys = [df_each_err[model].quantile(quant) for quant in (0.05, 0.25, 0.5, 0.75, 0.95)]

    fig.add_box(y=ys, name=model, width=0.7)

    # Add an annotation for the interquartile range
    IQR = ys[3] - ys[1]
    median = ys[2]
    fig.add_annotation(
        x=idx, y=1, text=f"{IQR:.2}", showarrow=False, yref="paper", yshift=-10
    )
    fig.add_annotation(
        x=idx,
        y=median,
        text=f"{median:.2}",
        showarrow=False,
        yshift=7,
        # bgcolor="rgba(0, 0, 0, 0.2)",
        # width=50,
    )
fig.add_annotation(x=-0.6, y=1, text="IQR", showarrow=False, yref="paper", yshift=-10)

fig.layout.legend.update(orientation="h", y=1.2)
# prevent x-labels from rotating
fig.layout.xaxis.tickangle = 0
# use line breaks to offset every other x-label
x_labels_with_offset = [
    f"{'<br>' * (idx % 2)}{label}" for idx, label in enumerate(models)
]
fig.layout.xaxis.update(tickvals=models, ticktext=x_labels_with_offset)
fig.show()


# %%
save_fig(fig, f"{SITE_FIGS}/box-hull-dist-errors.svelte")
fig.layout.showlegend = False
save_fig(fig, f"{PDF_FIGS}/box-hull-dist-errors.pdf")
