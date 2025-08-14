import { useParams, Link } from "react-router-dom";
import { useQuery} from "@tanstack/react-query";
import { LoadingWithText} from "../../../components/Loading/Loading.tsx";
import { ErrorWithText } from "../../../components/Error/Error.tsx";
import { LoanBadge, StatusBadge } from "../../../components/Badges/Badges.tsx";
import styles from "./ListingDetail.module.css";

type PricePoint = { price_id?: number; effective_date: string; price: number };
type ResponseItem = { response_id: number; author?: string | null; note_text?: string | null; created_at: string };

type Detail = {
    listing_id: number;

    // Address / property
    street: string;
    unit?: string | null;
    city: string;
    state: string;
    zip: string;
    beds?: number | null;
    baths?: number | null;
    sqft?: number | null;
    hoa_month?: number | null;
    latitude?: number | null;
    longitude?: number | null;

    // Listing
    date_added?: string | null;
    mls_link?: string | null;
    mls_status?: string | null;
    equity_to_cover?: number | null;
    sent_to_clients?: boolean | null;
    investor_ok?: boolean | null;

    // Realtor
    realtor_name: string;

    // Loan
    loan_type?: string | null;
    interest_rate?: number | null;
    balance?: number | null;
    piti?: number | null;
    loan_servicer?: string | null;
    investor_allowed?: boolean | null;

    // Price
    asking_price?: number | null;
    asking_price_date?: string | null;
    price_history: PricePoint[];

    // Analysis
    analysis_url?: string | null;
    roi_pass?: boolean | null;
    done_running_numbers?: boolean | null;
    analysis_run_date?: string | null;

    // Notes
    responses: ResponseItem[];
};

const fmtMoney = (n?: number | null) =>
  n == null ? "—" : new Intl.NumberFormat(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);

const fmtPct = (n?: number | null, frac = 3) =>
  n == null ? "—" : `${n.toFixed(frac)}%`;

const fmtDate = (d?: string | null) => (d ? new Date(d).toLocaleDateString() : "—");

const fullAddress = (d: Detail) =>
  `${d.street}${d.unit ? ` #${d.unit}` : ""}, ${d.city}, ${d.state} ${d.zip}`;

export default function ListingDetail() {
    const { id } = useParams();
    const { data, isLoading, error } = useQuery<Detail>({
        queryKey: ["listing", id],
        queryFn: async () => {
            const r = await fetch(`/pyapi/listings/${id}`, {
                credentials: "include",
            });
            if (!r.ok) throw new Error(await r.text());
            return r.json();
        },
    });

    if (isLoading) return <LoadingWithText text="listing" />;
    if (error || !data) return <ErrorWithText error="Failed to load listing" />;

    const d = data;
    return (
        <div className={styles.detail}>
            <Link to="/listings">Back to list</Link>

            <h2 className={styles.heading}>{fullAddress(d)}</h2>

            <div className={styles.chips}>
                <span className={styles.chip}>{d.date_added ? new Date(d.date_added).toLocaleDateString() : "—"}</span>
                <span className={styles.chip}>{d.realtor_name || "—"}</span>
                <LoanBadge value={d.loan_type} />
                {d.mls_status && <StatusBadge value={d.mls_status} />}
            </div>

            <div className={styles.actions}>
                {d.mls_link && (
                    <a
                        href={d.mls_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.linkBtn}
                    >
                        View on MLS
                    </a>
                )}
                {d.analysis_url && (
                    <a href={d.analysis_url} target="_blank" rel="noopener noreferrer" className={styles.linkBtn}>
                        Open Analysis
                    </a>
                )}
                <Link
                    to={`/map?focus=${d.listing_id}`}
                    className={styles.linkBtn}
                >
                    View on Map
                </Link>
            </div>

            <section className={styles.section}>
                <h3>Pricing, Equity &amp; Loans</h3>
                <dl className={styles.dl}>
                    <div className={styles.item}>
                        <dt className={styles.dt}>Interest Rate</dt>
                        <dd className={styles.dd}>{fmtPct(d.interest_rate, 3)}</dd>
                    </div>
                    <div className={styles.item}>
                        <dt className={styles.dt}>PITI</dt>
                        <dd className={styles.dd}>{fmtMoney(d.piti)}</dd>
                     </div>
                    <div className={styles.item}>
                        <dt className={styles.dt}>Asking Price</dt>
                        <dd className={styles.dd}>{fmtMoney(d.asking_price)}</dd>
                    </div>
                    <div className={styles.item}>
                        <dt className={styles.dt}>Assumable Balance</dt>
                        <dd className={styles.dd}>{fmtMoney(d.balance)}</dd>
                    </div>
                    <div className={styles.item}>
                        <dt className={styles.dt}>Equity to Cover</dt>
                        <dd className={styles.dd}>{fmtMoney(d.equity_to_cover)}</dd>
                    </div>
                </dl>
            </section>

            <section className={styles.section}>
                <h3>Notes</h3>
                {d.responses?.length ? (
                    <ul className={styles.list}>
                        {d.responses.map((r) => (
                            <li key={r.response_id}>
                                <div><strong>{r.author || "—"}</strong> • {fmtDate(r.created_at)}</div>
                                <div>{r.note_text || "—"}</div>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className={styles.empty}>No notes yet.</p>
                )}
            </section>

            <div className={styles.section}>
                <h3>Analysis &amp; Outreach</h3>
                <dl className={styles.dl}>
                    <div className={styles.item}>
                        <dt className={styles.dt}>Done running numbers?</dt>
                        <dd className={styles.dd}>{d.done_running_numbers ? "Yes" : "No"}</dd>
                    </div>
                    <div className={styles.item}>
                        <dt className={styles.dt}>Pass ROI criteria?</dt>
                        <dd className={styles.dd}>{d.roi_pass ? "Yes" : "No"}</dd>
                    </div>
                    <div className={styles.item}>
                        <dt className={styles.dt}>Sent to clients?</dt>
                        <dd className={styles.dd}>{d.sent_to_clients ? "Yes" : "No"}</dd>
                    </div>
                </dl>
            </div>

            <section className={styles.section}>
                <h3>Property Details</h3>
                <dl className={styles.dl}>
                    <div className={styles.item}>
                        <dt className={styles.dt}>Beds</dt>
                        <dd className={styles.dd}>{d.beds ?? "—"}</dd>
                    </div>
                    <div className={styles.item}>
                        <dt className={styles.dt}>Baths</dt>
                        <dd className={styles.dd}>{d.baths == null ? "—" : d.baths.toFixed(1)}</dd>
                    </div>
                    <div className={styles.item}>
                        <dt className={styles.dt}>Sqft</dt>
                        <dd className={styles.dd}>{d.sqft == null ? "—" : d.sqft.toLocaleString()}</dd>
                    </div>
                    <div className={styles.item}>
                        <dt className={styles.dt}>HOA / Month</dt>
                        <dd className={styles.dd}>{fmtMoney(d.hoa_month)}</dd>
                    </div>
                </dl>
            </section>

            <section className={styles.section}>
                <h3>Price History</h3>
                {d.price_history?.length ? (
                    <ul className={styles.list}>
                        {d.price_history.map((p) => (
                            <li key={p.price_id ?? `${p.effective_date}-${p.price}`}>
                                <strong>{fmtDate(p.effective_date)}</strong>: {fmtMoney(p.price)}
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className={styles.empty}>No price history.</p>
                )}
            </section>
        </div>
    );
}