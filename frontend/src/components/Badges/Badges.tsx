import clsx from "clsx";
import styles from "./Badges.module.css";

export function loanBadgeClass(lt?: string | null) {
    switch((lt || "").toUpperCase()) {
        case "NVVA": return styles.loanNvva;
        case "VA": return styles.loanVa;
        case "MAYBE_NVVA": return styles.loanMaybe;
        case "CONV": return styles.loanConv;
        case "FHA": return styles.loanFha;
        default: return "";
    }
}

export function statusBadgeClass(s?: string | null) {
    const v = (s || "").trim().toLowerCase();
    if (v.startsWith("active")) return styles.statusActive;
    if (v.startsWith("sold")) return styles.statusSold;
    if (v.startsWith("withdrawn")) return styles.statusWithdrawn;
    if (v.startsWith("pending")) return styles.statusPending;
    if (v.startsWith("under contract")) return styles.statusUnderContract;
    if (v.startsWith("cancelled") || v.startsWith("canceled")) return styles.statusCancelled;
    if (v.startsWith("expired")) return styles.statusExpired;
    if (v.startsWith("off market") || v.startsWith("off-market")) return styles.statusOffmarket;
    return "";
}

type BadgeProps = { value?: string | null; className?: string };

export function LoanBadge({ value, className }: BadgeProps) {
    return (
        <span className={clsx(styles.badge, loanBadgeClass(value), className)}>
            {value ?? "—"}
        </span>
    );
}

export function StatusBadge({ value, className }: BadgeProps) {
    return (
        <span className={clsx(styles.badge, statusBadgeClass(value), className)}>
            {value ?? "—"}
        </span>
    );
}