# Sample data

## `fuel_import_sample.csv`

A deliberately mixed fuel-import file for exercising the parser (F-402).
Assumes two vehicles exist:

- plate **B-100-AAA**, `tank_capacity_l = 50`, `current_km = 20000`
- plate **B-200-BBB**, `fuel_card_number = CARD-001`

Expected outcome (7 data rows):

| Row | Outcome | Reason |
|-----|---------|--------|
| 1 | imported | normal |
| 2 | imported | matched by fuel card |
| 3 | imported, **suspect** | 80 L > 50 L tank capacity |
| 4 | imported, **suspect** | odometer 19000 < last known 20000 |
| 5 | **rejected** | unknown vehicle (plate X-999-ZZZ) |
| 6 | **rejected** | invalid liters ("abc") |
| 7 | **rejected** | missing date |

→ `total_rows=7, imported_rows=4, rejected_rows=3`, with 2 suspects flagged.
