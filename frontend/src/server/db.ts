import { Pool } from "pg";

export const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    host: "localhost",
    port: 5432,
    database: "assumables",
    user: "assumables_user",
    password: "dev_pw",
    ssl: process.env.PGSSL?.toLowerCase() === "true" ? { rejectUnauthorized: false } : undefined,
    max: 10,
    idleTimeoutMillis: 30_000,
});

pool.on("error", (err) => {
    console.error("Unexpected PG pool error:", err);
});
