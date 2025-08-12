import sys, pathlib, pandas as pd
from sqlalchemy import create_engine, text

from etl.helpers.property  import split_address, parse_hoa, n2none
from etl.helpers.loan      import canon_loan_type
from etl.helpers.realtor   import split_realtors
from etl.maps              import rename_map

engine = create_engine("postgresql+psycopg://assumables_user:dev_pw@db:5432/assumables")

xlsx_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                         else "data/assumable_properties.xlsx")

df = pd.read_excel(xlsx_path, sheet_name="Assumable Properties MLS")
df = df.rename(columns=rename_map)

with engine.begin() as conn:
    for row in df.itertuples(index=False):
        # Realtor
        names = split_realtors(row.realtor)

        if not names:
            print("⚠️  no realtor name; skipping row:", row.addr)
            continue

        realtor_ids = []
        for nm in names:
            rid = conn.execute(
                text("""INSERT INTO realtor(name)
                        VALUES (:n)
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING realtor_id"""),
                {"n": nm}
            ).scalar()
            realtor_ids.append(rid)

        primary_realtor_id = realtor_ids[0]

        # Property
        if pd.isna(row.addr):
            continue

        parts = split_address(str(row.addr))
        if parts is None:
            print("bad address:", row.addr)
            continue

        prop_params = {
            **parts,
            "unit" : None,
            "beds" : n2none(row.beds),
            "baths": n2none(row.baths),
            "sqft" : n2none(row.sqft),
            "hoa"  : parse_hoa(row.hoa_month)
        }
        prop_id = conn.execute(
            text("""
                INSERT INTO property
                       (street, unit, city, state, zip,
                        beds, baths, sqft, hoa_month)
                VALUES (:street,:unit,:city,:state,:zip,
                        :beds, :baths, :sqft, :hoa)
                ON CONFLICT (street, unit, city, state, zip)
                DO UPDATE SET street = EXCLUDED.street
                RETURNING property_id
            """),
            prop_params
        ).scalar()

        # Listing
        mls_link  = row.mls_link
        mls_id    = mls_link.split("/")[-1] if pd.notna(mls_link) else None
        listing_id = conn.execute(
            text("""INSERT INTO listing(property_id, realtor_id, date_added,
                                         mls_link, mls_id, mls_status)
                    VALUES (:pid, :rid, :dt, :lnk, :mid, :status)
                    ON CONFLICT (mls_id) DO NOTHING
                    RETURNING listing_id"""),
            dict(pid=prop_id,
                 rid=primary_realtor_id,
                 dt = row.added.date() if pd.notna(row.added) else None,
                 lnk=mls_link,
                 mid=mls_id,
                 status=row.mls_status)
        ).scalar()
        if listing_id is None:
            continue

        # Price history
        if pd.notna(row.asking_price):
            conn.execute(
                text("INSERT INTO price_history(listing_id, price) "
                     "VALUES (:lid, :p)"),
                {"lid": listing_id, "p": row.asking_price}
            )

        # Loan (assumable mortgage)
        lt_code = canon_loan_type(row.assume_type)
        if lt_code is None:
            print("Unknown loan type:", row.assume_type, "— skipping loan row")
        else:
            loan_params = dict(
                pid=prop_id,
                lt=lt_code,
                ir=row.int_rate or None,
                bal=row.loan_bal or None,
                piti=row.piti or None,
                srv=row.loan_servicer or None,
                ok=str(row.invest_ok).strip().upper() in ('Y', 'YES', 'TRUE')
            )
            conn.execute(
                text("""INSERT INTO loan(property_id, loan_type, interest_rate,
                                          balance, piti, loan_servicer,
                                          investor_allowed)
                        VALUES (:pid,:lt,:ir,:bal,:piti,:srv,:ok)
                        ON CONFLICT DO NOTHING"""),
                loan_params
            )