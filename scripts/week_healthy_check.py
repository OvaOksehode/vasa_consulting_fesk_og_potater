# week_healthy_check.py
# Dag-for-dag helsesjekk for en uke: kvitteringer, linjer, enheter, ~omsetning og antall skift.
# Kjør:
#   python scripts/week_healthy_check.py 5
#   python scripts/week_healthy_check.py 5 --base C:\sti\til\prosjektrot

from pathlib import Path
import sys, json
from collections import Counter

# ===== FINN DATAMAPPEN (prosjektroten) =====
HERE = Path(__file__).resolve()
CANDIDATES = [HERE.parent.parent, Path.cwd()]
BASE = None
for c in CANDIDATES:
    if (c / "transactions").exists() and (c / "amounts").exists():
        BASE = c
        break
# Tillat manuell overstyring: --base <sti>
if "--base" in sys.argv:
    i = sys.argv.index("--base")
    try:
        BASE = Path(sys.argv[i + 1]).resolve()
        del sys.argv[i:i + 2]
    except Exception:
        pass
if BASE is None:
    print("Fant ikke data-roten (må inneholde 'transactions' og 'amounts').")
    sys.exit(1)

def jload(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- TRANSAKSJONER ----------
def pick_top_layer(data):
    """Velg ÉN toppkilde: dag->liste, .transactions, liste, dict-verdier."""
    if isinstance(data, dict) and data and all(isinstance(v, list) for v in data.values()):
        keys = sorted([int(k) for k in data.keys() if str(k).isdigit()])
        if keys:
            recs = []
            for k in keys:
                recs.extend([r for r in data[str(k)] if isinstance(r, dict)])
            return recs, keys
    if isinstance(data, dict) and isinstance(data.get("transactions"), list):
        return [r for r in data["transactions"] if isinstance(r, dict)], None
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)], None
    if isinstance(data, dict):
        return [v for v in data.values() if isinstance(v, dict)], None
    return [], None

def extract_lines(rec):
    """Streng prioritet: bruk KUN første strukturen som finnes i posten."""
    items = rec.get("items") or rec.get("products")
    if isinstance(items, list) and items and isinstance(items[0], dict):
        for it in items:
            name = it.get("item") or it.get("name") or it.get("product")
            qty  = it.get("qty") or it.get("quantity") or it.get("amount") or 1
            if name is not None:
                try:
                    yield str(name), float(qty)
                except:
                    pass
        return
    mt, ma = rec.get("merch_types"), rec.get("merch_amounts")
    if isinstance(mt, list) and isinstance(ma, list) and len(mt) == len(ma):
        for n, q in zip(mt, ma):
            if n is not None:
                try:
                    yield str(n), float(q)
                except:
                    pass
        return
    mk, ma2 = rec.get("merch_keys"), rec.get("merch_amounts")
    if isinstance(mk, list) and isinstance(ma2, list) and len(mk) == len(ma2):
        for n, q in zip(mk, ma2):
            if n is not None:
                try:
                    yield str(n), float(q)
                except:
                    pass
        return
    merch = rec.get("merch")
    if isinstance(merch, dict):
        for n, q in merch.items():
            if n is not None:
                try:
                    yield str(n), float(q if q is not None else 1)
                except:
                    pass
        return
    if isinstance(merch, list):
        for n in merch:
            if n is not None:
                yield str(n), 1.0

def load_prices_latest():
    """Hent siste kjente pris per vare (for omsetningsestimat)."""
    prices_dir = BASE / "prices"
    latest = {}
    if prices_dir.exists():
        for p in sorted(prices_dir.glob("prices_*.json")):
            try:
                data = jload(p)
                for k, v in data.items():
                    try:
                        latest[str(k)] = float(v)
                    except:
                        pass
            except:
                pass
    sp = BASE / "supplier_prices.json"
    if sp.exists():
        data = jload(sp)
        for k, v in data.items():
            latest.setdefault(str(k), float(v) if v is not None else 0.0)
    return latest

# ---------- SCHEDULES (robust parser) ----------
DAY_NAME_MAP = {
    "1":1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,
    "mon":1,"monday":1,"tue":2,"tuesday":2,"wed":3,"wednesday":3,
    "thu":4,"thursday":4,"fri":5,"friday":5,"sat":6,"saturday":6,"sun":7,"sunday":7
}
def to_day_int(k):
    s = str(k).strip().lower()
    s = s[:3] if s in ("monday","tuesday","wednesday","thursday","friday","saturday","sunday") else s
    return DAY_NAME_MAP.get(s, None)

def count_shifts_week(w):
    """
    Støtter:
      A) {"1":[{...},...], "2":[...]}
      B) {"1":{"shifts":[...]} , "2":{"shifts":[...]}}
      C) {"monday":[...], "tue":[...]} (dag-navn)
      D) [ {"day": 1, ...}, {"day": 1, ...}, ... ]  (ren liste med 'day'-felt)
    Returnerer (status, per_day Counter, diagnose-streng)
    """
    per_day = Counter()
    p = BASE / "schedules" / f"schedules_{w}.json"
    if not p.exists():
        return "mangler", per_day, f"{p.name} finnes ikke"

    try:
        data = jload(p)
    except Exception as e:
        return "feilformat", per_day, f"JSON-feil: {e}"

    diag = []
    if isinstance(data, dict):
        for k, v in data.items():
            d = to_day_int(k)
            if d is None:
                diag.append(f"ignorerer nøkkel '{k}'")
                continue
            # v kan være liste (shifts), eller dict med 'shifts'
            if isinstance(v, list):
                per_day[d] += len(v)
            elif isinstance(v, dict) and isinstance(v.get("shifts"), list):
                per_day[d] += len(v["shifts"])
            else:
                # ukjent form – prøv å telle "checkins" eller "entries" hvis finnes
                for key in ("checkins","entries"):
                    if isinstance(v, dict) and isinstance(v.get(key), list):
                        per_day[d] += len(v[key])
                        break
        if not per_day:
            return "tom/ukjent", per_day, "dict-lignende struktur men ikke gjenkjent"
        return "ok", per_day, "; ".join(diag) if diag else "ok"
    elif isinstance(data, list):
        # forventer elementer med 'day'
        had_day = False
        for entry in data:
            if not isinstance(entry, dict): 
                continue
            d = entry.get("day")
            if d is None: 
                continue
            try:
                d = int(d)
            except:
                d = to_day_int(d)
            if d is None:
                continue
            had_day = True
            per_day[d] += 1
        if not had_day:
            return "tom/ukjent", per_day, "liste uten 'day'-felt"
        return "ok", per_day, "ok"
    else:
        return "feilformat", per_day, f"uventet type: {type(data).__name__}"

# ---------- MAIN ----------
def main():
    # uke-argument (eller spør hvis mangler)
    if len(sys.argv) < 2:
        try:
            w = int(input("Hvilken uke vil du sjekke? ").strip())
        except Exception:
            print("Bruk: python scripts\\week_healthy_check.py <uke_index> [--base <sti_til_data>]"); return
    else:
        w = int(sys.argv[1])

    tx_path = BASE / "transactions" / f"transactions_{w}.json"
    if not tx_path.exists():
        print(f"Fant ikke {tx_path}")
        return

    data = jload(tx_path)
    records, day_keys_present = pick_top_layer(data)

    # per-dag aggregering
    per_day = {d: {"receipts": 0, "lines": 0, "qty": 0.0, "revenue": 0.0} for d in range(1, 8)}
    prices = load_prices_latest()

    if day_keys_present:  # eksplisitte dag-lister
        for d in day_keys_present:
            for rec in data[str(d)]:
                if not isinstance(rec, dict): 
                    continue
                line_count = 0
                for item, qty in extract_lines(rec):
                    per_day[d]["qty"] += qty
                    per_day[d]["revenue"] += qty * prices.get(item, 0.0)
                    line_count += 1
                per_day[d]["lines"] += line_count
                if line_count > 0:
                    per_day[d]["receipts"] += 1
    else:  # ingen dag-nøkler → legg i "0"
        per_day = {0: {"receipts": 0, "lines": 0, "qty": 0.0, "revenue": 0.0}}
        for rec in records:
            if not isinstance(rec, dict): 
                continue
            line_count = 0
            for item, qty in extract_lines(rec):
                per_day[0]["qty"] += qty
                per_day[0]["revenue"] += qty * prices.get(item, 0.0)
                line_count += 1
            per_day[0]["lines"] += line_count
            if line_count > 0:
                per_day[0]["receipts"] += 1

    # Schedules (robust)
    sched_status, shifts, sched_diag = count_shifts_week(w)

    # Utskrift
    print(f"\nUke {w} – kvitteringer, linjer, enheter, ~omsetning, skift")
    print("{:>3}  {:>9}  {:>7}  {:>10}  {:>12}  {:>7}".format("dag", "kvitt.", "linjer", "enheter", "omsetn.(~)", "skift"))
    print("-"*3, "-"*9, "-"*7, "-"*10, "-"*12, "-"*7)
    for d in sorted(per_day.keys()):
        row = per_day[d]
        print(f"{d:>3}  {row['receipts']:>9}  {row['lines']:>7}  {row['qty']:>10.0f}  {row['revenue']:>12.0f}  {shifts.get(d, 0):>7}")

    # Diagnose for schedules
    print(f"\nSchedules: {sched_status} ({sched_diag})")

    # Raske signaler
    days = [d for d in per_day if d != 0]
    dead = [d for d in days if per_day[d]["receipts"] == 0 and per_day[d]["qty"] == 0]
    if dead:
        if any(shifts.get(d, 0) > 0 for d in dead):
            print("• Døddager", dead, "men skift > 0 → sannsynlig POS/nett/registreringsfeil.")
        else:
            print("• Døddager", dead, "og skift = 0 → sannsynlig stengt/ingen bemanning.")
    other = [k for k in per_day.keys() if k not in range(1, 8)]
    if other and other != [0]:
        print("• Uvanlige dag-keys i data:", other, "→ sjekk dag-mapping (feil uke eller feil dager?).")
    last3 = sum(per_day.get(d, {"qty": 0})["qty"] for d in [5, 6, 7])
    first4 = sum(per_day.get(d, {"qty": 0})["qty"] for d in [1, 2, 3, 4])
    if last3 > 3 * max(1.0, first4):
        print("• Salg siste 3 dager >> første 4 → sen leveranse/promo/åpningstider i starten?")

if __name__ == "__main__":
    main()
