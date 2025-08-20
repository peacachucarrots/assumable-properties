import argparse, httpx, pandas as pd
from datetime import date
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .helpers.columns import normalize_cols, match_column
from .helpers.geocode import geocode_address_sync, QPSLimiter
from .helpers.type_conversion import to_float, to_decimal, to_int, to_date

from .helpers.address import parse_address
from .helpers.balances import backfill_balances_pass
from .helpers.booleans import parse_boolish
from .helpers.loans import map_loan_type, normalize_rate
from .helpers.mls import extract_mls_id
from .helpers.property_fees import parse_hoa_amount_and_freq
from .helpers.roi import parse_roi_pass_and_category

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx_path")
    ap.add_argument("--sheet", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--list-sheets", action="store_true")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--on-negative-equity", choices=["null","skip","zero","abs"], default="null")
    ap.add_argument("--skip-backfill", action="store_true", help="Skip the integrated balance backfill pass")
    ap.add_argument("--dry-run", action="store_true", help="Only affects backfill pass; main load still writes")
    args = ap.parse_args()

    xls = pd.ExcelFile(args.xlsx_path)
    if args.list_sheets:
        print("Sheets:")
        for s in xls.sheet_names: print(f"- {s}")
        return

    df = pd.read_excel(args.xlsx_path, sheet_name=(args.sheet or xls.sheet_names[0]))
    df.columns = normalize_cols(df.columns)
    cols = list(df.columns)

    want = [
        "Date Added","Realtor Name","MLS Listing link","Property Address",
        "Type of Assumable (FHA, VA, Non Veteran VA)","Assumable Interest Rate",
        "PITI","Asking Price","Assumable Loan Balance","Equity To Cover",
        "Response from Realtor/Seller","Done running numbers?",
        "Does it pass ROI number criteria?","Sent to clients",
        "Link to Property Analysis","Beds","Baths","Sqft","HOA/Month",
        "MLS Status","Loan Servicer","Allow investor to assume the VA loan?",
        "Full response from Amy"
    ]
    resolved = {w: match_column(cols, w) for w in want}
    if args.debug:
        print("Detected headers:")
        for c in cols: print("-", c)
        print("\nColumn mapping:")
        for k,v in resolved.items(): print(f"- {k} -> {v}")

    C = resolved
    engine: Engine = create_engine(args.db or "postgresql+psycopg2://assumables_user:dev_pw@localhost:5432/assumables")

    with engine.begin() as conn:
        geo_client = httpx.Client(timeout=8.0)
        geo_cache: dict[tuple, tuple[float, float] | None] = {}
        geo_rl = QPSLimiter(qps=8.0)
        conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name='property' AND column_name='hoa_amount') THEN
                    ALTER TABLE property ADD COLUMN hoa_amount numeric(12,2);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name='property' AND column_name='hoa_frequency') THEN
                    ALTER TABLE property ADD COLUMN hoa_frequency text
                        CHECK (hoa_frequency in ('Monthly','Quarterly','Semi-Annual','Annual'));
                END IF;
            END $$;
        """))

        try:
            conn.execute(text("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='uniq_listing_property_realtor_link'
                    ) THEN
                        CREATE UNIQUE INDEX uniq_listing_property_realtor_link
                        ON listing (property_id, realtor_id, COALESCE(mls_link, ''));
                    END IF;
                END $$;
            """))
        except Exception:
            pass

        for i, row in df.iterrows():
            sp = conn.begin_nested()
            try:
                date_added = to_date(row[C.get("Date Added")]) if C.get("Date Added") else None
                realtor_name = (str(row[C.get("Realtor Name")]).strip() if C.get("Realtor Name") and not pd.isna(row[C.get("Realtor Name")]) else None)
                mls_link = (str(row[C.get("MLS Listing link")]).strip() if C.get("MLS Listing link") and not pd.isna(row[C.get("MLS Listing link")]) else None)
                mls_id = extract_mls_id(mls_link) if mls_link else None
                addr_val = row[C.get("Property Address")] if C.get("Property Address") else None
                street, unit, city, state, zip_code = parse_address(addr_val) if addr_val else (None,None,None,None,None)

                loan_type = map_loan_type(row[C.get("Type of Assumable (FHA, VA, Non Veteran VA)")]) if C.get("Type of Assumable (FHA, VA, Non Veteran VA)") else None
                rate = normalize_rate(row[C.get("Assumable Interest Rate")]) if C.get("Assumable Interest Rate") else None
                piti = to_decimal(row[C.get("PITI")]) if C.get("PITI") else None
                asking_price = to_decimal(row[C.get("Asking Price")]) if C.get("Asking Price") else None
                balance_val = to_decimal(row[C.get("Assumable Loan Balance")]) if C.get("Assumable Loan Balance") else None
                equity = to_decimal(row[C.get("Equity To Cover")]) if C.get("Equity To Cover") else None

                resp_realtor = (str(row[C.get("Response from Realtor/Seller")]).strip() if C.get("Response from Realtor/Seller") and not pd.isna(row[C.get("Response from Realtor/Seller")]) else None)
                # booleans
                done_numbers = parse_boolish(row[C.get("Done running numbers?")]) if C.get("Done running numbers?") else None
                roi_pass, roi_category = parse_roi_pass_and_category(row[C.get("Does it pass ROI number criteria?")]) if C.get("Does it pass ROI number criteria?") else (None, None)
                sent_to_clients = parse_boolish(row[C.get("Sent to clients")]) if C.get("Sent to clients") else None
                analysis_link = (str(row[C.get("Link to Property Analysis")]).strip() if C.get("Link to Property Analysis") and not pd.isna(row[C.get("Link to Property Analysis")]) else None)

                beds = to_int(row[C.get("Beds")]) if C.get("Beds") else None
                baths = to_float(row[C.get("Baths")]) if C.get("Baths") else None
                sqft = to_int(row[C.get("Sqft")]) if C.get("Sqft") else None
                hoa_amount, hoa_freq = parse_hoa_amount_and_freq(row[C.get("HOA/Month")]) if C.get("HOA/Month") else (None,None)
                mls_status = (str(row[C.get("MLS Status")]).strip() if C.get("MLS Status") and not pd.isna(row[C.get("MLS Status")]) else None)
                loan_servicer = (str(row[C.get("Loan Servicer")]).strip() if C.get("Loan Servicer") and not pd.isna(row[C.get("Loan Servicer")]) else None)
                investor_allowed = parse_boolish(row[C.get("Allow investor to assume the VA loan?")]) if C.get("Allow investor to assume the VA loan?") else None
                amy_full = (str(row[C.get("Full response from Amy")]).strip() if C.get("Full response from Amy") and not pd.isna(row[C.get("Full response from Amy")]) else None)

                # Realtor
                realtor_id = None
                if realtor_name:
                    realtor_id = conn.execute(text("SELECT realtor_id FROM realtor WHERE name=:n"), {"n": realtor_name}).scalar()
                    if realtor_id is None:
                        realtor_id = conn.execute(text("INSERT INTO realtor(name) VALUES (:n) RETURNING realtor_id"), {"n": realtor_name}).scalar()

                # Property
                property_id = None
                if street or city or state or zip_code:
                    property_id = conn.execute(text("""
                        SELECT property_id FROM property
                         WHERE COALESCE(street,'')=:street
                           AND COALESCE(unit,'')=:unit
                           AND COALESCE(city,'')=:city
                           AND COALESCE(state,'')=:state
                           AND COALESCE(zip,'')=:zip
                    """), {"street": street or "", "unit": unit or "", "city": city or "", "state": state or "", "zip": zip_code or ""}).scalar()
                    if property_id is None:
                        property_id = conn.execute(text("""
                            INSERT INTO property (street, city, state, zip, unit, beds, baths, sqft, hoa_amount, hoa_frequency)
                            VALUES (:street,:city,:state,:zip,:unit,:beds,:baths,:sqft,:hoa_amount,:hoa_freq)
                            RETURNING property_id
                        """), {"street": street, "city": city, "state": state, "zip": zip_code, "unit": unit,
                               "beds": beds, "baths": float(baths) if baths is not None else None,
                               "sqft": sqft, "hoa_amount": float(hoa_amount) if hoa_amount is not None else None,
                               "hoa_freq": hoa_freq}).scalar()
                    else:
                        conn.execute(text("""
                            UPDATE property SET
                              beds = COALESCE(:beds, beds),
                              baths = COALESCE(:baths, baths),
                              sqft = COALESCE(:sqft, sqft),
                              hoa_amount = COALESCE(:hoa_amount, hoa_amount),
                              hoa_frequency = COALESCE(:hoa_freq, hoa_frequency)
                            WHERE property_id=:pid
                        """), {"beds": beds, "baths": float(baths) if baths is not None else None, "sqft": sqft,
                               "hoa_amount": float(hoa_amount) if hoa_amount is not None else None,
                               "hoa_freq": hoa_freq, "pid": property_id})

                # Geocode address
                if property_id and street and city and state and zip_code:
                    cache_key = (street.strip().upper(), (unit or "").strip().upper(),
                                 city.strip().upper(), state.strip().upper(), zip_code.strip())
                    coords = geo_cache.get(cache_key)
                    if coords is None:
                        geo_rl.wait()
                        coords = geocode_address_sync(
                            geo_client, street.strip(), city.strip(), state.strip(), zip_code.strip(), unit
                        )
                        geo_cache[cache_key] = coords

                    if coords:
                        lat, lon = coords
                        conn.execute(text("""
                            UPDATE property
                                SET latitude = :lat, longitude = :lon
                            WHERE property_id=:pid
                                AND (latitude IS DISTINCT FROM :lat OR longitude IS DISTINCT FROM :lon)
                        """), {"pid": property_id, "lat": lat, "lon": lon})

                # Listing
                listing_id = None
                if property_id and realtor_id:
                    if equity is not None and equity < 0:
                        mode = args.on_negative_equity
                        if mode == "skip":
                            sp.commit(); continue
                        elif mode == "zero":
                            equity_val = 0.0
                        elif mode == "abs":
                            equity_val = float(abs(equity))
                        else:
                            equity_val = None
                    else:
                        equity_val = float(equity) if equity is not None else None

                    listing_id = conn.execute(text("""
                        SELECT listing_id FROM listing
                         WHERE property_id=:pid AND realtor_id=:rid AND COALESCE(mls_link,'')=COALESCE(:link,'')
                    """), {"pid": property_id, "rid": realtor_id, "link": mls_link}).scalar()

                    if listing_id is None:
                        listing_id = conn.execute(text("""
                            INSERT INTO listing (property_id, realtor_id, date_added, mls_id, mls_link, mls_status, equity_to_cover, sent_to_clients)
                            VALUES (:pid,:rid,:date_added,:mls_id,:mls_link,:mls_status,:equity,:sent)
                            RETURNING listing_id
                        """), {"pid": property_id, "rid": realtor_id, "date_added": date_added, "mls_id": mls_id,
                               "mls_link": mls_link, "mls_status": mls_status, "equity": equity_val,
                               "sent": sent_to_clients}).scalar()
                    else:
                        conn.execute(text("""
                            UPDATE listing SET
                              date_added = COALESCE(:date_added,date_added),
                              mls_id = COALESCE(:mls_id,mls_id),
                              mls_status = COALESCE(:mls_status,mls_status),
                              equity_to_cover = COALESCE(:equity,equity_to_cover),
                              sent_to_clients = COALESCE(:sent,sent_to_clients)
                            WHERE listing_id=:lid
                        """), {"date_added": date_added, "mls_id": mls_id, "mls_status": mls_status,
                               "equity": equity_val, "sent": sent_to_clients, "lid": listing_id})

                # Loan
                if property_id:
                    exists = conn.execute(text("SELECT loan_id FROM loan WHERE property_id=:pid"), {"pid": property_id}).scalar()
                    loan_type_eff = loan_type or "CONV"
                    balance_num = float(balance_val) if balance_val is not None else None
                    if exists is None:
                        conn.execute(text("""
                            INSERT INTO loan (property_id, loan_type, interest_rate, balance, piti, loan_servicer, investor_allowed)
                            VALUES (:pid,:loan_type,:rate,:balance,:piti,:servicer,:allowed)
                        """), {"pid": property_id, "loan_type": loan_type_eff, "rate": float(rate) if rate is not None else None,
                               "balance": balance_num, "piti": float(piti) if piti is not None else None,
                               "servicer": loan_servicer, "allowed": investor_allowed})
                    else:
                        conn.execute(text("""
                            UPDATE loan SET
                              loan_type = COALESCE(:loan_type, loan_type),
                              interest_rate = COALESCE(:rate, interest_rate),
                              balance = COALESCE(:balance, balance),
                              piti = COALESCE(:piti, piti),
                              loan_servicer = COALESCE(:servicer, loan_servicer),
                              investor_allowed = COALESCE(:allowed, investor_allowed)
                            WHERE property_id=:pid
                        """), {"pid": property_id, "loan_type": loan_type_eff,
                               "rate": float(rate) if rate is not None else None,
                               "balance": balance_num, "piti": float(piti) if piti is not None else None,
                               "servicer": loan_servicer, "allowed": investor_allowed})

                # Price
                if listing_id and asking_price is not None:
                    eff_date = date_added or date.today()
                    exists_price = conn.execute(text("""
                        SELECT price_id FROM price_history
                         WHERE listing_id=:lid AND price=:price AND effective_date=:eff
                    """), {"lid": listing_id, "price": float(asking_price), "eff": eff_date}).scalar()
                    if exists_price is None:
                        conn.execute(text("""
                            INSERT INTO price_history (listing_id, effective_date, price)
                            VALUES (:lid,:eff,:price)
                        """), {"lid": listing_id, "eff": eff_date, "price": float(asking_price)})

                # Analysis
                if listing_id and (analysis_link or done_numbers is not None or roi_pass is not None or roi_category):
                    exists_analysis = conn.execute(text("""
                        SELECT analysis_id
                          FROM analysis
                         WHERE listing_id = :lid
                           AND ((:u IS NULL AND url IS NULL) OR url = :u)
                         ORDER BY run_date DESC, analysis_id DESC
                         LIMIT 1
                    """), {"lid": listing_id, "u": analysis_link}).scalar()

                    if exists_analysis is None:
                        conn.execute(text("""
                            INSERT INTO analysis (listing_id, url, roi_category, roi_pass, run_complete)
                            VALUES (:lid, :url, :cat, :roi, :done)
                        """), {"lid": listing_id, "url": analysis_link, "cat": roi_category,
                               "roi": roi_pass, "done": done_numbers})
                    else:
                        conn.execute(text("""
                            UPDATE analysis
                               SET url = COALESCE(:url, url),
                                   roi_category = COALESCE(:cat, roi_category),
                                   roi_pass = COALESCE(:roi, roi_pass),
                                   run_complete = COALESCE(:done, run_complete)
                             WHERE analysis_id = :aid
                        """), {"aid": exists_analysis, "url": analysis_link,
                               "cat": roi_category, "roi": roi_pass, "done": done_numbers})

                # Responses
                if listing_id and resp_realtor:
                    conn.execute(text("""
                        INSERT INTO response (listing_id, author, note_text)
                        VALUES (:lid,'Realtor/Seller',:note)
                    """), {"lid": listing_id, "note": resp_realtor})
                if listing_id and amy_full:
                    conn.execute(text("""
                        INSERT INTO response (listing_id, author, note_text)
                        VALUES (:lid,'Amy',:note)
                    """), {"lid": listing_id, "note": amy_full})

                sp.commit()
            except Exception as e:
                sp.rollback()
                print(f"Row {i} error: {e}")

        if not args.skip_backfill:
            col_addr = C.get("Property Address")
            col_bal  = C.get("Assumable Loan Balance")
            updated, inserted_stub, skipped = backfill_balances_pass(
                conn, df, col_addr=col_addr, col_bal=col_bal, dry_run=args.dry_run
            )
            print(f"Backfill pass: updated={updated}, inserted_stub={inserted_stub}, skipped={skipped}")
        else:
            print("Backfill pass skipped by flag.")

    geo_client.close()
    print("Done.")

if __name__ == "__main__":
    main()
