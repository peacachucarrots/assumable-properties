export type Address = { street: string; unit?: string|null; city: string; state: string; zip: string };

type GeocodeResponse = {
    status: string;
    results?: Array<{
        partial_match?: boolean;
        types?: string[];
        geometry: {
            location: { lat: number; lng: number };
            location_type?: "ROOFTOP" | "RANGE_INTERPOLATED" | "GEOMETRIC_CENTER" | "APPROXIMATE";
            viewport?: any;
        };
    }>;
    error_message?: string;
};

export async function geocodeAddress(a: Address) {
    const key = process.env.GOOGLE_MAPS_KEY;
    if (!key) {
        console.warn("No API Key.");
        return null;
    }

    const line1 = `${a.street}${a.unit ? " " + a.unit : ""}`;
    const freeform = `${line1}, ${a.city}, ${a.state} ${a.zip}, USA`;

    const params = new URLSearchParams({
        address: freeform,
        components: `country:US|postal_code:${a.zip}`,
        region: "us",
        key,
    });

    const url = `https://maps.googleapis.com/maps/api/geocode/json?${params.toString()}`;
    const res = await fetch(url);
    if (!res.ok) {
        console.warn("Geocode HTTP error", res.status);
        return null;
    }

    const data = (await res.json()) as GeocodeResponse;

    if (data.status !== "OK" || !data.results?.length) {
        console.warn("google geocode status", data.status, data.error_message || "");
        return null;
    }

    const score = (r: GeocodeResponse["results"][number]) => {
        const t = r.geometry.location_type || "APPROXIMATE";
        const locTypeScore =
            t === "ROOFTOP" ? 4 :
                t === "RANGE_INTERPOLATED" ? 3 :
                    t === "GEOMETRIC_CENTER" ? 2 : 1;
        const partialPenalty = r.partial_match ? -2 : 0;
        const streetAddressBonus = (r.types || []).includes("street_address") ? 1 : 0;
        return locTypeScore + partialPenalty + streetAddressBonus;
    };

    const best = [...data.results].sort((a, b) => score(b) - score(a))[0];
    const { lat, lng } = best.geometry.location;
    return Number.isFinite(lat) && Number.isFinite(lng) ? { lat, lon: lng } : null;
}