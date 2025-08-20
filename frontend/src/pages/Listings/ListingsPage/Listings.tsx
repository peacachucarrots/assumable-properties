import { useQuery } from "@tanstack/react-query";
import { useSearchParams, Link} from "react-router-dom";
import { LoadingWithText } from "../../../components/Loading/Loading.tsx";
import { ErrorWithText } from "../../../components/Error/Error";
import styles from "./Listings.module.css";
import {LoanBadge, StatusBadge} from "../../../components/Badges/Badges.tsx";

type Listing = {
    listing_id: number;
    address: string;
    price: number | null;
    loan_type: string | null;
    mls_status: string | null;
};

const LOAN_TYPES = ["NVVA", "Maybe_NVVA", "VA", "FHA", "CONV"];
const STATUSES = [
    "Active",
    "Pending",
    "Sold",
    "Under Contract",
    "Withdrawn",
    "Cancelled",
    "Expired",
    "Off Market",
];

const fmtMoney = (n: number | null | undefined) =>
    n == null ? "—" : new Intl.NumberFormat(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);

function loanFilterClass(lt: string, checked: boolean) {
    const classes = [styles.checkItem];
    if (checked) classes.push(styles.checked);

    switch (lt.toUpperCase()) {
        case "NVVA":        classes.push(styles.optNvva); break;      // green
        case "VA":          classes.push(styles.optVa); break;        // red
        case "MAYBE_NVVA":  classes.push(styles.optMaybe); break;     // yellow
        case "CONV":        classes.push(styles.optConv); break;      // gray
        case "FHA":         classes.push(styles.optFha); break;       // purple
    }
    return classes.join(" ");
}

function statusFilterClass(st: string, checked: boolean, styles: any) {
    const classes = [styles.checkItem];
    if (checked) classes.push(styles.checked);
    const v = st.toLowerCase();
    if (v.startsWith("active")) classes.push(styles.optActive);
    else if (v.startsWith("sold")) classes.push(styles.optSold);
    else if (v.startsWith("withdrawn")) classes.push(styles.optWithdrawn);
    else if (v.startsWith("pending")) classes.push(styles.optPending);
    else if (v.startsWith("under contract")) classes.push(styles.optUnderContract);
    else if (v.startsWith("cancelled") || v.startsWith("canceled")) classes.push(styles.optCancelled);
    else if (v.startsWith("expired")) classes.push(styles.optExpired);
    else if (v.startsWith("off market") || v.startsWith("off-market")) classes.push(styles.optOffmarket);
    return classes.join(" ");
}

const statusMatches = (filterVal: string, actual?: string | null) =>
    !!actual && actual.trim().toLowerCase().startsWith(filterVal.trim().toLowerCase());

export default function Listings() {
    const [searchParams, setSearchParams] = useSearchParams();
    const selectedLoanTypes = searchParams.getAll("loan_type");
    const selectedStatuses = searchParams.getAll("mls_status");

    function updateMulti(name: string, values: string[]) {
        const next = new URLSearchParams(searchParams);
        next.delete(name);
        values.forEach(v => next.append(name, v));
        setSearchParams(next, { replace: false });
    }

    function toggleLoanType(val: string) {
        const next = selectedLoanTypes.includes(val)
            ? selectedLoanTypes.filter(v => v !== val)
            : [...selectedLoanTypes, val];
        updateMulti("loan_type", next);
    }

    function toggleStatus(val: string) {
        const next = selectedStatuses.includes(val)
            ? selectedStatuses.filter(v => v !== val)
            : [...selectedStatuses, val];
        updateMulti("mls_status", next);
    }

    const qs =
                selectedLoanTypes.length === 0
                    ? ""
                    : "?" + new URLSearchParams(selectedLoanTypes.map((v) => ["loan_type", v])).toString();

    const { data, isLoading, error } = useQuery<Listing[]>({
        queryKey: ["listings", selectedLoanTypes],
        keepPreviousData: true,
        queryFn: () => {
            return fetch(`/api/listings${qs}`, { credentials: "include" })
                .then((r) => {
                    if (!r.ok) throw new Error("API error");
                    return r.json();
                });
        },
    });

    const rows = (data ?? []).filter(l =>
        selectedStatuses.length === 0
            ? true
            : selectedStatuses.some(s => statusMatches(s, l.mls_status))
    );

    return (
        <div className={styles.page}>
            <aside className={styles.sidebar}>
                <div className={styles.filtersCard}>
                    <h2 className={styles.filtersTitle}>Filters</h2>

                    <fieldset className={styles.filterSection}>
                        <legend className={styles.sectionTitle}>
                            Loan types {selectedLoanTypes.length ? `(${selectedLoanTypes.length})` : "(all)"}
                        </legend>

                        <div className={styles.checkList}>
                            {LOAN_TYPES.map((lt) => {
                                const checked = selectedLoanTypes.includes(lt);
                                return (
                                    <label key={lt} className={loanFilterClass(lt, checked)}>
                                        <input
                                            type="checkbox"
                                            className={styles.srOnly}
                                            value={lt}
                                            checked={checked}
                                            onChange={() => toggleLoanType(lt)}
                                        />
                                        <LoanBadge value={lt} />
                                    </label>
                                );
                            })}
                        </div>

                        {selectedLoanTypes.length > 0 && (
                            <button
                                type="button"
                                className={styles.clearBtn}
                                onClick={() => updateMulti("loan_type", [])}
                            >
                                Clear all
                            </button>
                        )}
                    </fieldset>

                    <fieldset className={styles.filterSection}>
                        <legend className={styles.sectionTitle}>
                            MLS Status {selectedStatuses.length ? `(${selectedStatuses.length})` : "(all)"}
                        </legend>
                        <div className={styles.checkList}>
                            {STATUSES.map(st => {
                                const checked = selectedStatuses.includes(st);
                                return (
                                    <label key={st} className={statusFilterClass(st, checked, styles)}>
                                        <input
                                            type="checkbox"
                                            className={styles.srOnly}
                                            value={st}
                                            checked={checked}
                                            onChange={() => toggleStatus(st)}
                                        />
                                        <StatusBadge value={st} />
                                    </label>
                                );
                            })}
                        </div>
                        {selectedStatuses.length > 0 && (
                            <button type="button" className={styles.clearBtn} onClick={() => updateMulti("mls_status", [])}>
                                Clear statuses
                            </button>
                        )}
                    </fieldset>
                </div>
            </aside>

            <main className={styles.content}>
                {isLoading && <LoadingWithText text="listings" />}
                {error && <ErrorWithText error="listings" />}

                {rows.length > 0 ? (
                <div className={styles.table}>
                    <div className={`${styles.row} ${styles.headerRow}`} aria-hidden="true">
                        <div className={styles.colHead}>Address</div>
                        <div className={`${styles.colHead} ${styles.right}`}>Price</div>
                        <div className={styles.colHead}>Loan Type</div>
                        <div className={styles.colHead}>MLS Status</div>
                    </div>

                    {rows.map(l => (
                        <Link to={`/listing/${l.listing_id}`} key={l.listing_id} className={styles.row}>
                            <div className={styles.cellAddress}>{l.address}</div>
                            <div className={`${styles.cellPrice} ${styles.right}`}>{fmtMoney(l.price)}</div>
                            <div className={styles.cellLoan}><LoanBadge value={l.loan_type} /></div>
                            <div className={styles.cellStatus}><StatusBadge value={l.mls_status} /></div>
                        </Link>
                    ))}
                </div>
            ) : (
                !isLoading && !error && <p className={styles.empty}>No listings found.</p>
            )}
            </main>
        </div>
    );
}