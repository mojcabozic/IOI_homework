from pathlib import Path
from pyaxis import pyaxis
import json
import re

px_file = Path("poraba_energije.px")

result = pyaxis.parse(
    str(px_file),
    encoding="windows-1250",
)

df = result["DATA"].copy()

MESECI = {
    1: "januar", 2: "februar", 3: "marec", 4: "april",
    5: "maj", 6: "junij", 7: "julij", 8: "avgust",
    9: "september", 10: "oktober", 11: "november", 12: "december",
}

def format_mesec(label: str) -> str:
    # "2026M07 (začasni podatki)" -> "Julij 2026"
    year, month = re.match(r"(\d{4})M(\d{2})", label).groups()
    return f"{MESECI[int(month)]} {year}"

records = [
    {"mesec": format_mesec(m), "poraba": int(float(p))}
    for m, p in zip(df["MESEC"], df["DATA"])
]

with open("poraba_energije.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
