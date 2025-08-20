import {Link, NavLink, useNavigate} from "react-router-dom";
import {useMutation, useQueryClient} from "@tanstack/react-query";
import styles from "./Navbar.module.css";

export default function Navbar() {
    const navigate = useNavigate();
    const qc = useQueryClient();

    const logout = useMutation({
        mutationFn: async () => {
            await fetch("/api/auth/logout", {
                method: "POST",
                credentials: "include"
            });
        },
        onSuccess: async () => {
            await qc.cancelQueries();
            qc.clear();
            navigate("/", { replace: true });
        }
    });

    return (
        <nav className={styles.nav} aria-label="Primary">
            <div className={styles.inner}>
                <Link to="/" className={styles.brand}>Assumables</Link>

                <div className={styles.links}>
                    <NavLink
                        to="/listings"
                        className={({ isActive }) =>
                            isActive ? `${styles.link} ${styles.active}` : styles.link
                        }
                    >
                        Listings
                    </NavLink>

                    <NavLink
                        to="/map"
                        className={({ isActive }) =>
                            isActive ? `${styles.link} ${styles.active}` : styles.link
                        }
                    >
                        Map
                    </NavLink>

                    <NavLink
                        to="/AddListing"
                        className={({ isActive }) =>
                            isActive ? `${styles.link} ${styles.active}` : styles.link
                        }
                    >
                        Add Listing
                    </NavLink>
                </div>

                <div className={styles.right}>
                    <button
                        className="btn btn--secondary"
                        onClick={() => logout.mutate()}
                        disabled={logout.isPending}
                        title="Logout"
                    >
                        {logout.isPending ? "Logging out..." : "Logout"}
                    </button>
                </div>
            </div>
        </nav>
    );
}