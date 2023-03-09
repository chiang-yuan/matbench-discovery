# %%
import os

import pandas as pd
from aviary.wren.utils import get_aflow_label_from_spglib
from mp_api.client import MPRester
from pymatviz.utils import annotate_mae_r2
from tqdm import tqdm

from matbench_discovery import today
from matbench_discovery.data import DATA_FILES

"""
Download all MP formation and above hull energies on 2023-01-10.

Related EDA of MP formation energies:
https://github.com/janosh/pymatviz/blob/main/examples/mp_bimodal_e_form.ipynb
"""

__author__ = "Janosh Riebesell"
__date__ = "2023-01-10"

module_dir = os.path.dirname(__file__)


# %%
fields = {
    "material_id",
    "formula_pretty",
    "formation_energy_per_atom",
    "energy_per_atom",
    "symmetry",
    "energy_above_hull",
    "decomposition_enthalpy",
    "energy_type",
}

with MPRester(use_document_model=False) as mpr:
    docs = mpr.thermo.search(fields=fields, thermo_types=["GGA_GGA+U"])

assert fields == set(docs[0]), f"missing fields: {fields - set(docs[0])}"
print(f"{today}: {len(docs) = :,}")
# 2022-08-13: len(docs) = 146,323
# 2023-01-10: len(docs) = 154,718


# %%
df = pd.DataFrame(docs).set_index("material_id")

df.energy_type.value_counts().plot.pie(backend="plotly", autopct="%1.1f%%")
# GGA: 72.2%, GGA+U: 27.8%


# %%
df["spacegroup_number"] = [x["number"] for x in df.pop("symmetry")]

df["wyckoff_spglib"] = [get_aflow_label_from_spglib(x) for x in tqdm(df.structure)]

df.to_csv(DATA_FILES.mp_energies)
# df = pd.read_csv(DATA_FILES.mp_energies)


# %% reproduce fig. 1b from https://arxiv.org/abs/2001.10591 (as data consistency check)
ax = df.plot.scatter(
    x="formation_energy_per_atom",
    y="decomposition_enthalpy",
    alpha=0.1,
    xlim=[-5, 1],
    ylim=[-1, 1],
    color=(df.decomposition_enthalpy > 0).map({True: "red", False: "blue"}),
    title=f"{today} - {len(df):,} MP entries",
)

annotate_mae_r2(df.formation_energy_per_atom, df.decomposition_enthalpy)
# result on 2023-01-10: plots match. no correlation between formation energy and
# decomposition enthalpy. R^2 = -1.571, MAE = 1.604
# ax.figure.savefig(f"{module_dir}/mp-decomp-enth-vs-e-form.webp", dpi=300)


# %% scatter plot energy above convex hull vs decomposition enthalpy
# https://berkeleytheory.slack.com/archives/C16RE1TUN/p1673887564955539
mask_above_line = df.energy_above_hull - df.decomposition_enthalpy.clip(0) > 0.1
ax = df.plot.scatter(
    x="decomposition_enthalpy",
    y="energy_above_hull",
    color=mask_above_line.map({True: "red", False: "blue"})
    # backend="plotly",
    # hover_data=["index", "formula_pretty", "formation_energy_per_atom"],
)
# most points lie on line y=x for x > 0 and y = 0 for x < 0.
n_above_line = sum(mask_above_line)
ax.set(
    title=f"{n_above_line:,} / {len(df):,} = {n_above_line/len(df):.1%} "
    "MP materials with\nenergy_above_hull - decomposition_enthalpy.clip(0) > 0.1"
)
# ax.figure.savefig(f"{module_dir}/mp-e-above-hull-vs-decomp-enth.webp", dpi=300)
