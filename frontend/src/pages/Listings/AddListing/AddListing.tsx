import {useNavigate} from "react-router-dom";
import {useState} from "react";
import styles from "./AddListing.module.css";
import {ErrorWithText} from "../../../components/Error/Error";

function numOrNull(v: FormDataEntryValue | null | undefined): number | null {
    if (v == null) return null;
    const s = String(v).trim();
    if (s === "") return null;
    const cleaned = s.replace(/^\$/, "").replace(/[,\s]/g, "");
    const n = Number(cleaned);
    return Number.isFinite(n) ? n : null;
}

export default function AddListing() {
    const navigate = useNavigate();
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setError(null);

        const fd = new FormData(e.currentTarget);
        const zip = String(fd.get("zip") || "").trim();
        const state = String(fd.get("state") || "CO").trim().toUpperCase();
        const street = String(fd.get("street") || "").trim();
        const city = String(fd.get("city") || "").trim();

        if (!street || !city || !state || !zip) {
            setError("Please fill Street, City, State, and ZIP.");
            return;
        }
        if (!/^\d{5}(-\d{4})?$/.test(zip)) {
            setError("ZIP must be 5 digits (optionally +4).");
            return;
        }

        const today = new Date().toISOString().slice(0, 10);

        const hf = String(fd.get("hoa_frequency") || "").trim();

        const data = {
            // Address / property
            street,
            unit: (String(fd.get("unit") || "").trim() || null),
            city,
            state,
            zip,
            beds: numOrNull(fd.get("beds")),
            baths: numOrNull(fd.get("baths")),
            sqft: numOrNull(fd.get("sqft")),
            hoa_amount: numOrNull(fd.get("hoa_amount")),
            hoa_frequency: hf === "" ? null : hf,

            // Realtor
            realtor_name: String(fd.get("realtor_name") || "").trim() || "Unknown",

            // Listing
            date_added: (String(fd.get("date_added") || "") || today),
            mls_link: (String(fd.get("mls_link") || "").trim() || null),
            mls_status: (String(fd.get("mls_status") || "").trim() || null),
            sent_to_clients: fd.get("sent_to_clients") === "on",

            // Loan
            loan_type: (String(fd.get("loan_type") || "").trim() || undefined),
            interest_rate: numOrNull(fd.get("interest_rate")),
            balance: numOrNull(fd.get("balance")),
            piti: numOrNull(fd.get("piti")),
            loan_servicer: (String(fd.get("loan_servicer") || "").trim() || null),

            // Price
            asking_price: numOrNull(fd.get("asking_price")),

            // Analysis
            analysis_url: (String(fd.get("analysis_url") || "").trim() || null),
            done_running_numbers: fd.get("done_running_numbers") === "on",
            roi_pass: fd.get("roi_pass") === "on",

            // Notes
            response_from_realtor: (String(fd.get("response_from_realtor") || "").trim() || null),
            full_response_from_amy: (String(fd.get("full_response_from_amy") || "").trim() || null),
        };

        setSaving(true);
        try {
            const res = await fetch("/api/listings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify(data),
            });
            if (!res.ok) {
                let detail = "";
                try {
                    const j = await res.clone().json();
                    detail = j?.message || j?.error || j?.detail || j?.step || JSON.stringify(j);
                } catch {
                    try { detail = await res.text(); } catch { /* ignore */ }
                }
                throw new Error(`Request failed (${res.status}) ${detail || ""}`.trim());
            }
            const json = await res.json();
            if (json?.id) {
                navigate(`/listing/${json.id}`);
            } else {
                navigate("/listings");
            }
        } catch (err: any) {
            setError(err?.message || "Something went front saving the listing.");
            console.error("create_listing_error:", err);
        } finally {
            setSaving(false);
        }
    }

    const today = new Date().toISOString().slice(0, 10);

    return (
        <div className={styles.page}>
            <div className={styles.card}>
                <h1 className={styles.title}>Add Listing</h1>

                <form className={styles.form} onSubmit={onSubmit} noValidate>
                    <h2 className={styles.section}>Address</h2>
                    <div className={styles.row}>
                        <label htmlFor="street">Street<span className={styles.req}>*</span> </label>
                        <input id="street" name="street" placeholder="123 Main St" required />
                    </div>
                    <div className={styles.row2}>
                        <div>
                            <label htmlFor="unit">Unit</label>
                            <input id="unit" name="unit" placeholder="123" />
                        </div>
                        <div>
                            <label htmlFor="city">City<span className={styles.req}>*</span></label>
                            <input id="city" name="city" placeholder="Colorado Springs" required />
                        </div>
                        <div className={styles.stateZip}>
                            <div>
                                <label htmlFor="state">State<span className={styles.req}>*</span></label>
                                <input id="state" name="state" defaultValue="CO" maxLength={2} required />
                            </div>
                            <div>
                                <label htmlFor="zip">ZIP<span className={styles.req}>*</span></label>
                                <input id="zip" name="zip" placeholder="80829" inputMode="numeric" pattern="\d{5}(-\d{4})?" required />
                            </div>
                        </div>
                    </div>

                    <h2 className={styles.section}>Property</h2>
                    <div className={styles.row2}>
                        <div>
                            <label htmlFor="beds">Beds</label>
                            <input id="beds" name="beds" placeholder="2" type="number" min="0" step="1" />
                        </div>
                        <div>
                            <label htmlFor="baths">Baths</label>
                            <input id="baths" name="baths" placeholder="2" type="number" min="0" step="0.5" />
                        </div>
                        <div>
                            <label htmlFor="sqft">Sq Ft</label>
                            <input id="sqft" name="sqft" placeholder="1750" type="number" min="0" step="1" />
                        </div>
                        <div>
                            <label htmlFor="hoa_amount">HOA ($)</label>
                            <input id="hoa_amount" name="hoa_amount" placeholder="250" type="number" min="0" step="1" />
                        </div>
                        <div>
                            <label htmlFor="hoa_frequency">HOA Frequency</label>
                            <select id="hoa_frequency" name="hoa_frequency" defaultValue="">
                                <option value="">— Select —</option>
                                <option>Monthly</option>
                                <option>Quarterly</option>
                                <option>Semi-Annual</option>
                                <option>Annual</option>
                            </select>
                        </div>
                    </div>

                    <h2 className={styles.section}>Listing (MLS)</h2>
                    <div className={styles.row2}>
                        <div>
                            <label htmlFor="date_added">Date Added</label>
                            <input id="date_added" name="date_added" type="date" defaultValue={today} />
                        </div>
                        <div>
                            <label htmlFor="mls_status">MLS Status</label>
                            <select id="mls_status" name="mls_status" defaultValue="">
                                <option value="">— Select —</option>
                                <option>Active</option>
                                <option>Pending</option>
                                <option>Sold</option>
                                <option>Under Contract</option>
                                <option>Withdrawn</option>
                                <option>Cancelled</option>
                                <option>Expired</option>
                                <option>Off Market</option>
                            </select>
                        </div>
                        <div>
                            <label htmlFor="mls_link">MLS Link</label>
                            <input id="mls_link" name="mls_link" placeholder="https://portal.onehome.com/..." />
                        </div>
                    </div>

                    <h2 className={styles.section}>Pricing</h2>
                    <div className={styles.row2}>
                        <div>
                            <label htmlFor="asking_price">Asking Price ($)</label>
                            <input id="asking_price" name="asking_price" type="number" min="0" step="1" placeholder="500000" />
                        </div>
                        <div className={styles.checkboxWrap}>
                            <label className={styles.checkbox}>
                                <input id="sent_to_clients" name="sent_to_clients" type="checkbox" /> Sent to clients
                            </label>
                        </div>
                        <div />
                        <div />
                    </div>

                    <h2 className={styles.section}>Loan (Assumable)</h2>
                    <div className={styles.row2}>
                        <div>
                            <label htmlFor="loan_type">Type</label>
                            <select id="loan_type" name="loan_type" defaultValue="">
                                <option value="">— Select —</option>
                                <option value="FHA">FHA</option>
                                <option value="VA">VA</option>
                                <option value="NVVA">Non-Veteran VA</option>
                                <option value="Maybe_NVVA">Maybe NVVA</option>
                                <option value="CONV">Conventional</option>
                            </select>
                        </div>
                        <div>
                            <label htmlFor="interest_rate">Assumable Interest Rate (%)</label>
                            <input id="interest_rate" name="interest_rate" type="number" min="0" step="1" placeholder="2.750" />
                        </div>
                        <div>
                            <label htmlFor="piti">PITI ($/mo)</label>
                            <input id="piti" name="piti" type="number" min="0" step="1" placeholder="2250" />
                        </div>
                        <div>
                            <label htmlFor="balance">Assumable Loan Balance ($)</label>
                            <input id="balance" name="balance" type="number" min="0" step="1" placeholder="345000" />
                        </div>
                    </div>
                    <div className={styles.row2}>
                        <div>
                            <label htmlFor="loan_servicer">Loan Servicer</label>
                            <input id="loan_servicer" name="loan_servicer" placeholder="PennyMac" />
                        </div>
                        <div />
                        <div />
                    </div>

                    <h2 className={styles.section}>Analysis</h2>
                    <div className={styles.row2}>
                        <div className={styles.checkboxWrap}>
                            <label className={styles.checkbox}>
                                <input id="done_running_numbers" name="done_running_numbers" type="checkbox" />
                                Done running numbers?
                            </label>
                        </div>
                        <div className={styles.checkboxWrap}>
                            <label className={styles.checkbox}>
                                <input id="roi_pass" name="roi_pass" type="checkbox" />
                                Pass ROI criteria?
                            </label>
                        </div>
                        <div>
                            <label htmlFor="analysis_url">Link to Property Analysis</label>
                            <input id="analysis_url" name="analysis_url" placeholder="https://docs.google.com/..." />
                        </div>
                        <div />
                    </div>

                    <h2 className={styles.section}>Notes</h2>
                    <div className={styles.row}>
                        <label htmlFor="realtor_name">Realtor Name</label>
                        <input id="realtor_name" name="realtor_name" placeholder="Ryan Thomson" />
                    </div>
                    <div className={styles.row}>
                        <label htmlFor="response_from_realtor">Response from Realtor/Seller</label>
                        <textarea id="response_from_realtor" name="response_from_realtor" rows={3} />
                    </div>
                    <div className={styles.row}>
                        <label htmlFor="full_response_from_amy">Full response from Amy</label>
                        <textarea id="full_response_from_amy" name="full_response_from_amy" rows={3} />
                    </div>

                    {error && <ErrorWithText error={error} />}

                    <div className={styles.actions}>
                        <button className="btn" type="submit" disabled={saving}>
                            {saving ? "Saving..." : "Save Listing"}
                        </button>
                    </div>

                    <p className="hint">
                        Property coordinates will be auto-filled after saving.
                    </p>
                </form>
            </div>
        </div>
    );
}