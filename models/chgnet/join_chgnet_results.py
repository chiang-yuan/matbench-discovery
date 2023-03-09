"""Concatenate CHGNet results from multiple data files generated by slurm job array
into single file.
"""


# %%
from __future__ import annotations

import os
import warnings
from glob import glob

import pandas as pd
from pymatviz import density_scatter
from tqdm import tqdm

from matbench_discovery import today
from matbench_discovery.data import as_dict_handler
from matbench_discovery.energy import get_e_form_per_atom
from matbench_discovery.preds import df_preds, e_form_col

__author__ = "Janosh Riebesell"
__date__ = "2023-03-01"

warnings.filterwarnings(action="ignore", category=UserWarning, module="pymatgen")


# %%
module_dir = os.path.dirname(__file__)
task_type = "IS2RE"
date = "2023-03-06"
glob_pattern = f"{date}-chgnet-wbm-{task_type}*/*.json.gz"
file_paths = sorted(glob(f"{module_dir}/{glob_pattern}"))
print(f"Found {len(file_paths):,} files for {glob_pattern = }")

dfs: dict[str, pd.DataFrame] = {}


# %%
for file_path in tqdm(file_paths):
    if file_path in dfs:
        continue
    df = pd.read_json(file_path).set_index("material_id")
    # drop trajectory to save memory
    dfs[file_path] = df.drop(columns="chgnet_trajectory")

df_chgnet = pd.concat(dfs.values()).round(4)


# %% compute corrected formation energies
e_form_chgnet_col = "e_form_per_atom_chgnet"
df_chgnet["formula"] = df_preds.formula
df_chgnet[e_form_chgnet_col] = [
    get_e_form_per_atom(dict(energy=ene, composition=formula))
    for formula, ene in tqdm(
        df_chgnet.set_index("formula").chgnet_energy.items(), total=len(df_chgnet)
    )
]
df_preds[e_form_chgnet_col] = df_chgnet[e_form_chgnet_col]


# %%
ax = density_scatter(df=df_preds, x=e_form_col, y=e_form_chgnet_col)


# %%
out_path = f"{module_dir}/{today}-chgnet-wbm-{task_type}.json.gz"
df_chgnet = df_chgnet.round(4)
df_chgnet.select_dtypes("number").to_csv(out_path.replace(".json.gz", ".csv"))
df_chgnet.reset_index().to_json(out_path, default_handler=as_dict_handler)

# in_path = f"{module_dir}/2023-03-04-chgnet-wbm-IS2RE.json.gz"
# df_chgnet = pd.read_csv(in_path.replace(".json.gz", ".csv")).set_index("material_id")
# df_chgnet = pd.read_json(in_path).set_index("material_id")
