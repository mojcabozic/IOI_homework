"""Combine SURS average food prices (PX) and monthly electricity use (JSON) into one JSON file.

Output format (one object per year):
[
  {"leto": 2020, "poraba_energije": ..., "cena_hrane": ...},
  {"leto": 2021, "poraba_energije": ..., "cena_hrane": ...},
  ...
]
poraba_energije = sum of the monthly values in the energy JSON for that year
cena_hrane      = mean of the average annual retail prices (EUR) over all 48 products

Usage:
    pip install pyaxis pandas
    python make_json.py
"""
import json
import sys

import pandas as pd
from pyaxis import pyaxis

ENCODING = "windows-1250"

PRICES_PX = "cene_zivil_2018_2025.px"
ENERGY_JSON = "poraba_energije.json"
OUT_JSON = "podatki.json"


def load_prices(path: str) -> pd.Series:
    """Mean price over all products for each year."""
    df = pyaxis.parse(path, encoding=ENCODING)["DATA"].copy()
    # Columns: [product, measure, year, "DATA"] -> pick year and value by position.
    df = df.iloc[:, [-2, -1]]
    df.columns = ["leto", "value"]
    df["leto"] = df["leto"].astype(int)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.groupby("leto")["value"].mean().rename("cena_hrane")


def load_energy(path: str) -> pd.Series:
    """Yearly sum of the monthly 'poraba' values ('mesec' looks like 'januar 2020')."""
    with open(path, encoding="utf-8") as f:
        df = pd.DataFrame(json.load(f))
    df["leto"] = df["mesec"].str.split().str[-1].astype(int)

    # Sum monthly kWh values and convert to GWh
    yearly = df.groupby("leto")["poraba"].sum() / 1_000_000

    return yearly.rename("poraba_energije")


def main(prices_px: str, energy_json: str, out_json: str) -> None:
    prices = load_prices(prices_px)
    energy = load_energy(energy_json)

    # Prices cover 2018-2025, energy 2020-2026 -> inner join keeps the overlap (2020-2025)
    merged = pd.concat([energy, prices], axis=1, join="inner").sort_index()

    result = [
    {
        "leto": int(leto),
        "poraba_energije": round(float(row["poraba_energije"]), 6),
        "cena_hrane": round(float(row["cena_hrane"]), 2),
    }
    for leto, row in merged.iterrows()
]

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out_json} with {len(result)} years")


if __name__ == "__main__":
    prices_px = sys.argv[1] if len(sys.argv) > 1 else PRICES_PX
    energy_json = sys.argv[2] if len(sys.argv) > 2 else ENERGY_JSON
    out_json = sys.argv[3] if len(sys.argv) > 3 else OUT_JSON
    main(prices_px, energy_json, out_json)