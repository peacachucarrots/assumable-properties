import { useParams, Link } from "react-router-dom";
import { useQuery} from "@tanstack/react-query";
import styles from "./ListingDetail.module.css";
import { LoadingWithText} from "../../../components/Loading/Loading.tsx";
import { ErrorWithText } from "../../../components/Error/Error.tsx";

type Detail = {
    listing_id: number;
    address: string;
    price: number;
    loan_type: string;
    mls_status: string | null;
    beds: number | null;
    baths: number | null;
    sqft: number | null;
    interest_rate: number | null;
    balance: number | null;
    piti: number | null;
    realtor_name: string | null;
    date_added: string | null;
    mls_link: string | null;
};

export default function ListingDetail() {
    const { id } = useParams();
    const { data, isLoading, error } = useQuery<Detail>({
        queryKey: ["listing", id],
        queryFn: () => fetch(`/api/listings/${id}`)
            .then((r) => {
                if (!r.ok) throw new Error("API error");
                return r.json();
            })
    });

    if (isLoading) return <LoadingWithText text="listing" />;
    if (error) return <ErrorWithText text="listing" />;

    const d = data!;
    return (
        <div className={styles.detail}>
            <Link to="/listings">Back to list</Link>

            <h2 className={styles.heading}>{d.address}</h2>

            <dl className={styles.dl}>
                {[
                    ["Price", d.price ? `$${d.price.toLocaleString()}` : "—"],
                    ["Loan type", d.loan_type],
                    ["Status", d.mls_status ?? "—"],
                    ["Beds", d.beds ?? "—"],
                    ["Baths", d.baths ?? "—"],
                    ["Sqft", d.sqft?.toLocaleString() ?? "—"],
                    ["Interest rate", d.interest_rate ? `${d.interest_rate}%` : "—"],
                    ["Balance", d.balance?.toLocaleString() ?? "—"],
                    ["PITI", d.piti?.toLocaleString() ?? "—"],
                    ["Realtor", d.realtor_name ?? "—"],
                    [
                        "Date added",
                        d.date_added ? new Date(d.date_added).toLocaleDateString() : "—",
                    ],
                ].map(([label, value]) => (
                    <div className={styles.item} key={label}>
                        <dt className={styles.dt}>{label}</dt>
                        <dd className={styles.dd}>{value}</dd>
                    </div>
                ))}
            </dl>

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
        </div>
    );
}