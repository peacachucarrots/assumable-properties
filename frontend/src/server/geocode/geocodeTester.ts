import type { Request, Response } from "express";
import { geocodeAddress } from "./geocode.ts";

export async function geocodeTester(req: Request, res: Response) {
    const { street, unit, city, state, zip } = req.query as Record<string, string>;
    if (!street || !city || !state || !zip) {
        return res.status(400).json({ error: "street, city, state, zip are required" });
    }
    try {
        const coords = await geocodeAddress({
            street: String(street),
            unit: unit ? String(unit) : null,
            city: String(city),
            state: String(state),
            zip: String(zip),
        });
        res.json({ query: { street, unit, city, state, zip }, result: coords });
    } catch (e: any) {
        res.status(500).json({ error: e.message });
    }
}