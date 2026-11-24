"""Recalculate chamber ranks from Pietro Canini's published contrasts."""
import json
from urllib.request import urlopen

BASE = "https://www.accadradinuovo.com/Lab/giza_sar/prova_camere/file/"


def rank(row):
    return sum(abs(row["D"]) > abs(control) for control in row["controls_D"])


def main():
    for name in ("ESITO.json", "ESITO_APPENDICE_1000.json"):
        with urlopen(BASE + name, timeout=60) as source:
            data = json.load(source)
        eligible = [r for r in data["calibration_table"]
                    if r["D"] is not None and len(r["controls_D"]) >= 16]
        chosen = max(eligible, key=lambda r: (rank(r), abs(r["D"])))
        print(name, "calibration sign:", "+" if chosen["D"] > 0 else "-")
        for date, rooms in data["predictions"].items():
            if "Y_raw" in date:
                continue
            for room, row in rooms.items():
                if row["D"] is None:
                    print(date, room, "undefined")
                    continue
                count = len(row["controls_D"])
                found = count >= 16 and rank(row) == count and row["D"] * chosen["D"] > 0
                print(date, room, f"{rank(row)}/{count}", "pass" if found else "miss")


if __name__ == "__main__":
    main()
