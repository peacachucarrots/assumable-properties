import type { Request, Response } from "express";
import { pool } from "../db.ts";
import {geocodeAddress} from "../geocode/geocode.ts";

export async function postListing(req: Request, res: Response) {
    const client = await pool.connect();
    try {
        await client.query("BEGIN");

        const p = req.body;

        const realtor = await client.query(
            `INSERT INTO realtor (name)
             VALUES ($1)
             ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
             RETURNING realtor_id`,
            [p.realtor_name?.trim() || "Unknown"]
        );
        const realtor_id = realtor.rows[0].realtor_id;

        const prop = await client.query(
            `INSERT INTO property (street, unit, city, state, zip, beds, baths, sqft, hoa_month)
             VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
             ON CONFLICT (street, unit, city, state, zip)
             DO UPDATE SET beds = COALESCE(EXCLUDED.beds, property.beds),
                           baths = COALESCE(EXCLUDED.baths, property.baths),
                           sqft = COALESCE(EXCLUDED.sqft, property.sqft),
                           hoa_month = COALESCE(EXCLUDED.hoa_month, property.hoa_month)
             RETURNING property_id`,
            [
                p.street?.trim(),
                p.unit?.trim() || null,
                p.city?.trim(),
                (p.state || "CO").trim().toUpperCase(),
                p.zip?.trim(),
                p.beds ?? null,
                p.baths ?? null,
                p.sqft ?? null,
                p.hoa_month ?? null
            ]
        );
        const property_id = prop.rows[0].property_id;

        const { rows: cur } = await client.query(
            `SELECT latitude, longitude FROM property WHERE property_id = $1`,
            [property_id]
        );
        const haveCoords = cur[0]?.latitude != null && cur[0]?.longitude != null;

        if (!haveCoords) {
            const coords = await geocodeAddress({
                street: p.street,
                unit: p.unit,
                city: p.city,
                state: p.state,
                zip: p.zip,
            });

            if (coords) {
                await client.query(
                    'UPDATE property SET latitude = $1, longitude = $2 WHERE property_id = $3',
                    [coords.lat, coords.lon, property_id]
                );
            }
        }

        const askingPrice = p.asking_price ?? null;
        const loanBalance = p.balance ?? null;
        const equityToCover =
            askingPrice != null && loanBalance != null
                ? Math.max(0, Number((askingPrice - loanBalance).toFixed(2)))
                : null;

        const listing = await client.query(
            `INSERT INTO listing (property_id, realtor_id, date_added, mls_link, mls_status, equity_to_cover, sent_to_clients)
             VALUES ($1,$2,$3,$4,$5,$6,$7)
             RETURNING listing_id`,
            [
                property_id,
                realtor_id,
                p.date_added || new Date().toISOString().slice(0,10),
                p.mls_link || null,
                p.mls_status || null,
                equityToCover || null,
                !!p.sent_to_clients
            ]
        );
        const listing_id = listing.rows[0].listing_id;

        if (p.asking_price != null) {
            await client.query(
                `INSERT INTO price_history (listing_id, effective_date, price)
                 VALUES ($1, $2, $3)`,
                [
                    listing_id,
                    p.date_added || new Date().toISOString().slice(0, 10),
                    p.asking_price
                ]
            );
        }

        await client.query(
            `INSERT INTO loan (property_id, loan_type, interest_rate, balance, piti, loan_servicer, investor_allowed)
             VALUES ($1,$2,$3,$4,$5,$6,$7)
             ON CONFLICT (property_id) DO UPDATE SET
                loan_type = EXCLUDED.loan_type,
                interest_rate = EXCLUDED.interest_rate,
                balance = EXCLUDED.balance,
                piti = EXCLUDED.piti,
                loan_servicer = EXCLUDED.loan_servicer,
                investor_allowed = EXCLUDED.investor_allowed;`,
            [
                property_id,
                p.loan_type,
                p.interest_rate ?? null,
                p.balance ?? null,
                p.piti ?? null,
                p.loan_servicer || null,
                !!p.investor_allowed
            ]
        );

        if (p.done_running_numbers != null || p.roi_pass != null || p.analysis_url) {
            await client.query(
                `INSERT INTO analysis (listing_id, url, roi_pass, run_complete)
                 VALUES ($1,$2,$3,$4)`,
                [listing_id, p.analysis_url || null, !!p.roi_pass, !!p.done_running_numbers]
            );
        }

        const notes: Array<{author:string; text:string}> = [];
        if (p.response_from_realtor) notes.push({author: "Realtor/Seller", text: p.response_from_realtor.trim()});
        if (p.full_response_from_amy) notes.push({author: "Amy", text: p.full_response_from_amy.trim()});
        for (const n of notes) {
            await client.query(
                `INSERT INTO response (listing_id, author, note_text) VALUES ($1, $2, $3)`,
                [listing_id, n.author, n.text]
            );
        }

        await client.query("COMMIT");
        res.json({ id: listing_id });
    } catch (err: any) {
        await client.query("ROLLBACK");
        res.status(400).send(err.message || "Failed to create listing");
    } finally {
        client.release();
    }
}