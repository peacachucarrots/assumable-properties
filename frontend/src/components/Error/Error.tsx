import styles from "./Error.module.css";

export default function Error() {
    return <p>Error detected...</p>;
}

export function ErrorWithText({ error }: {error: string}) {
    return <p className={styles.error}>Error Message: {error}</p>;
}