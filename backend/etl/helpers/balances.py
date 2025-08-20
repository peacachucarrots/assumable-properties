from sqlalchemy import text

from .type_conversion import to_decimal
from .address import parse_address

def backfill_balances_pass(conn, df, col_addr, col_bal, dry_run=False):
    if not col_addr or not col_bal:
        print("Backfill: missing column mapping for address or balance; skipping.")
        return (0, 0, 0)

    updated, inserted_stub, skipped = 0, 0, 0
    for _, row in df.iterrows():
        addr = row[col_addr]
        bal = to_decimal(row[col_bal])
        if bal is None or not isinstance(addr, str) or not addr.strip():
            skipped += 1
            continue
        street, unit, city, state, zip_code = parse_address(addr)
        if not any([street, city, state, zip_code]):
            skipped += 1
            continue

        pid = conn.execute(text("""
            SELECT property_id FROM property
             WHERE COALESCE(street,'') = COALESCE(:street,'')
               AND COALESCE(unit,'')   = COALESCE(:unit,'')
               AND COALESCE(city,'')   = COALESCE(:city,'')
               AND COALESCE(state,'')  = COALESCE(:state,'')
               AND COALESCE(zip,'')    = COALESCE(:zip,'')
        """), {"street": street, "unit": unit, "city": city, "state": state, "zip": zip_code}).scalar()
        if pid is None:
            skipped += 1
            continue

        loan_id = conn.execute(text("SELECT loan_id FROM loan WHERE property_id = :pid"), {"pid": pid}).scalar()
        if loan_id is None:
            if dry_run:
                inserted_stub += 1
            else:
                conn.execute(text("INSERT INTO loan (property_id, loan_type, balance) VALUES (:pid, 'CONV', :bal)"),
                             {"pid": pid, "bal": float(bal)})
                inserted_stub += 1
        else:
            if dry_run:
                updated += 1
            else:
                conn.execute(text("UPDATE loan SET balance = :bal WHERE property_id = :pid"),
                             {"pid": pid, "bal": float(bal)})
                updated += 1

    return (updated, inserted_stub, skipped)