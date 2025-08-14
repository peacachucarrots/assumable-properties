import { fileURLToPath } from "node:url";
import path from "node:path";
import dotenv from "dotenv";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, "../../../.env") });

import express from "express";
import cors from "cors";
import {postListing} from "./routes/listings.ts";
import { pool } from "./db";
import {geocodeTester} from "./geocode/geocodeTester.ts";

pool.query("select 1 as ok")
  .then(() => console.log("DB connected"))
  .catch((e) => console.error("DB connect failed:", e));

const app = express();
app.use(cors());
app.use(express.json());

app.use("/api", (req, _res, next) => {
    console.log(`[API] ${req.method} ${req.url}`);
    next();
});

app.get("/api/dev/geocode", geocodeTester);

app.post("/api/listings", postListing);

app.listen(3000, () => console.log("API on http://localhost:3000"));