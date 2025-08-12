import {useEffect, useState} from "react";
import {useNavigate} from "react-router-dom";
import {useQueryClient} from "@tanstack/react-query";
import styles from "./Home.module.css";


export default function Home() {
    const qc = useQueryClient();
    const [token, setToken] = useState("");
    const [error, setError] = useState("");
    const [busy, setBusy]   = useState(false);
    const nav = useNavigate();

    useEffect(() => {
        fetch("/api/auth/me", { credentials: "include"}).then((r) => {
            if (r.ok) nav("/listings", { replace: true });
        });
    }, [nav]);

    async function onSubmit(e: React.FormEvent) {
        e.preventDefault();
        setBusy(true);
        setError("");
        const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ token })
        });
        if (res.ok) {
            qc.setQueryData(["auth", "me"], true);
            nav("/listings", { replace: true });
        } else {
            const msg = (await res.json().catch(() => null))?.detail ?? "Invalid token";
            setError(msg);
        }
        setBusy(false);
    }

    return (
        <div className={styles.container}>
            <div className={styles.formCard}>
                <form onSubmit={onSubmit} className={styles.form}>
                    <label className={styles.label}>
                        Access token
                        <input
                            className={styles.input}
                            type="password"
                            value={token}
                            onChange={(e) => setToken(e.target.value)}
                            required
                            autoComplete="off"
                        />
                    </label>
                    <button type="submit" disabled={busy} className={styles.button}>
                        {busy ? "Checking..." : "Submit"}
                    </button>
                    {error && <p className={styles.error}>{error}</p>}
                </form>
            </div>
        </div>
    );
}