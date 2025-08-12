import { useQuery } from "@tanstack/react-query";
import { useSearchParams, Link} from "react-router-dom";
import { LoadingWithText } from "../../../components/Loading/Loading.tsx";
import { ErrorWithText } from "../../../components/Error/Error";
import styles from "./Listings.module.css";

type Listing = {
    listing_id: number;
    address: string;
    price: number;
    loan_type: string;
    mls_status: string;
};

const LOAN_TYPES = ["FHA", "VA", "NVVA", "Maybe_NVVA", "CONV"];

export default function Listings() {
    const [searchParams, setSearchParams] = useSearchParams();
    const selected = searchParams.getAll("loan_type");

    function updateSelection(values: string[]) {
        if (values.length === 0) {
            searchParams.delete("loan_type");
            setSearchParams(searchParams, { replace: false });
        } else {
            setSearchParams(
                values.map((v) => ["loan_type", v]),
                { replace: false }
            );
        }
    }

    function handleCheckbox(e: React.ChangeEvent<HTMLInputElement>) {
        const val = e.target.value;
        const next = selected.includes(val)
            ? selected.filter((v) => v !== val)
            : [...selected, val];
        updateSelection(next);
    }

    const qs =
                selected.length === 0
                    ? ""
                    : "?" + new URLSearchParams(selected.map((v) => ["loan_type", v])).toString();

    const { data, isLoading, error } = useQuery<Listing[]>({
        queryKey: ["listings", selected],
        keepPreviousData: true,
        queryFn: () => {
            return fetch(`/api/listings${qs}`, { credentials: "include" })
                .then((r) => {
                    if (!r.ok) throw new Error("API error");
                    return r.json();
                });
        },
    });

    return (
        <div>
            <details className="ui-dropdown">
                <summary className="ui-summary">
                    Loan types {selected.length ? `(${selected.length})` : "(all)"}
                </summary>

                <div className="ui-menu" role="menu" aria-label="Loan type filters">
                    {LOAN_TYPES.map((lt) => (
                        <label
                            key={lt}
                            className="ui-menu__item"
                            role="menuitemcheckbox"
                            aria-checked={selected.includes(lt)}>
                            <input
                                className="ui-menu__checkbox"
                                type="checkbox"
                                value={lt}
                                checked={selected.includes(lt)}
                                onChange={handleCheckbox}
                            />
                            {lt}
                        </label>
                    ))}
                    {selected.length > 0 && (
                        <button
                            type="button"
                            className="btn--link ui-menu__action"
                            onClick={() => updateSelection([])}
                        >
                            Clear all
                        </button>
                    )}
                </div>
            </details>

            {isLoading && <LoadingWithText text="listings" />}
            {error && <ErrorWithText text="listings" />}

            {data && (
                <div className="grid-auto">
                    {data.map(l => (
                        <Link to={`/listing/${l.listing_id}`}
                              key={l.listing_id}
                              className="card"
                        >
                            <h3 className={styles.address}>{l.address}</h3>

                            <p className={styles.metaRow}>
                                <span className="muted">Price:</span>{" "}
                                <span className={styles.value}>
                                    {l.price ? `$${l.price.toLocaleString()}` : "-"}
                                </span>
                            </p>

                            <p className={styles.metaRow}>
                                <span className="muted">Loan type:</span>
                                <span className={styles.value}> {l.loan_type}</span>
                            </p>

                            <p className={styles.metaRow}>
                                <span className="muted">Status:</span>
                                <span className={styles.value}> {l.mls_status ?? "-"}</span>
                            </p>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}