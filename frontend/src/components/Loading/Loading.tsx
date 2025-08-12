import styles from "./Loading.module.css";

export default function Loading() {
    return (
        <p className={styles.loading}>Loading...</p>
    );
}

export function LoadingWithText({ text }: { text: string }) {
    return (
        <div className={styles.pageCenter}>
            <p className={styles.loading}>Loading {text}...</p>
        </div>
    )
}