
import json
import re
from pathlib import Path

import pandas as pd
from pyaxis import pyaxis


BASE_DIR = Path(__file__).resolve().parent

PRICE_FILE = BASE_DIR / "cene_zivil_1997_2017.px"
ENERGY_FILE = BASE_DIR / "poraba_energije_1996_2018.px"
FOOD_FILE = BASE_DIR / "zivila_na_gospodinjstvo_2000_2018.px"

OUTPUT_FILE = BASE_DIR / "output.json"


def read_px(filename):
    """Parse a local PC-Axis file with pyaxis."""
    parsed = pyaxis.parse(
        str(filename),
        encoding="windows-1250",
        lang="sl",
    )

    data = parsed["DATA"]

    # pyaxis versions may return a DataFrame or a dictionary.
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        df = pd.DataFrame(data)

    print(f"\n{filename.name}")
    print("Columns:", df.columns.tolist())
    print(df.head())

    return df, parsed.get("METADATA", {})


def find_column(df, *keywords):
    """Find a column using case-insensitive partial matches."""
    for col in df.columns:
        normalized = str(col).casefold()
        if all(word.casefold() in normalized for word in keywords):
            return col

    raise ValueError(
        f"Cannot find a column matching {keywords}. "
        f"Available columns: {df.columns.tolist()}"
    )


def to_number(series):
    """Convert numeric values while handling missing markers."""
    return pd.to_numeric(
        series.astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def extract_year(series):
    """Handle years such as 2000 and months such as 1997M01."""
    return (
        series.astype(str)
        .str.extract(r"(\d{4})", expand=False)
        .pipe(pd.to_numeric, errors="coerce")
        .astype("Int64")
    )


def annual_energy():
    df, _ = read_px(ENERGY_FILE)

    # Select the total final energy consumption measurement.
    df = df[
        df["MERITVE"].astype(str).str.contains(
            "Končna raba - skupaj", case=False, na=False
        )
    ]

    df["leto"] = extract_year(df["LETO"])
    df["energija"] = to_number(df["DATA"])

    return (
        df.dropna(subset=["leto", "energija"])
        .groupby("leto")["energija"]
        .sum()
    )


def annual_food_consumption():
    df, _ = read_px(FOOD_FILE)

    year_col = find_column(df, "LETO")

    # pyaxis commonly represents the PX stub dimension as a column.
    food_col = find_column(df, "ŽIVILA, PIJAČE")

    value_col = find_column(df, "DATA")

    df["leto"] = extract_year(df[year_col])
    df["poraba"] = to_number(df[value_col])

    # Mean across the food categories for each year.
    return (
        df.dropna(subset=["leto", "poraba"])
        .groupby("leto")["poraba"]
        .mean()
    )


def annual_food_prices():
    df, _ = read_px(PRICE_FILE)

    month_col = find_column(df, "MESEC")
    value_col = find_column(df, "DATA")

    df["leto"] = extract_year(df[month_col])
    df["cena"] = to_number(df[value_col])

    # Average all product prices and months for each year.
    return (
        df.dropna(subset=["leto", "cena"])
        .groupby("leto")["cena"]
        .mean()
    )


def main():
    energy = annual_energy()
    prices = annual_food_prices()

    # Complete this after inspecting the food file's columns.
    consumption = annual_food_consumption()

    print("\nEnergy years:", energy.index.tolist())
    print("Price years:", prices.index.tolist())
    print("Consumption years:", consumption.index.tolist())

    print("\nEnergy sample:")
    print(energy.head())

    print("\nPrice sample:")
    print(prices.head())

    print("\nConsumption sample:")
    print(consumption.head())

    result = pd.concat(
        [
            energy.rename("energija"),
            prices.rename("povprecna_cena_hrane"),
            consumption.rename("povprecna_poraba_hrane"),
        ],
        axis=1,
    )

    result.index.name = "leto"
    result = result.reset_index()

    # Keep only years with all three measurements.
    result = result.dropna(
        subset=[
            "energija",
            "povprecna_cena_hrane",
            "povprecna_poraba_hrane",
        ]
    )

    result["leto"] = result["leto"].astype(int)

    records = result.to_dict(orient="records")

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(records)} records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
