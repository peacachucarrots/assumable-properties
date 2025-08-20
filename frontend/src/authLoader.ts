import { redirect } from "react-router-dom";

export async function authLoader() {
    const res = await fetch("/api/auth/me", { credentials: "include" });
    if (res.ok) return null;
    throw redirect("/");
}