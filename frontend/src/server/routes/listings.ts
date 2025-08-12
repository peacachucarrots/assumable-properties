import type { Request, Response } from "express";

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
             DO UPDATE SET beds = EXCLUDED.beds,
                           baths = EXCLUDED.baths,
                           sqft = EXCLUDED.sqft,
                           hoa_month = EXCLUDED.hoa_month
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

        const listing = await client.query(
            `INSERT INTO listing (property_id, realtor_id, date_added, mls_link, mls_status, equity_to_cover, sent_to_clients, investor_ok)
             VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
             RETURNING listing_id`,
            [
                property_id,
                realtor_id,
                p.date_added || new Date().toISOString().slice(0,10),
                p.mls_link || null,
                p.mls_status || null,
                p.equity_to_cover || null,
                !!p.sent_to_clients,
                !!p.investor_allowed
            ]
        );
        const listing_id = listing.rows[0].listing_id;

        if (p.asking_price != null) {
            await client.query(
                `INSERT INTO price_history (listing_id, effective_date, price)
                 VALUES ($1, $2, $3)`,
                [listing_id, p.date_added || new Date().toISOString().slice(0, 10), p.asking_price]
            );
        }

        await client.query(
            `INSERT INTO loan (property_id, loan_type, interest_rate, balance, piti, loan_servicer, investor_allowed)
             VALUES ($1,$2,$3,$4,$5,$6,$7)
             ON CONFLICT DO NOTHING`,
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
        if (p.response_from_realtor) notes.push({author: "Realtor/Seller", text: p.response_from_realtor});
        if (p.full_response_from_amy) notes.push({author: "Amy", text: p.full_response_from_amy});
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