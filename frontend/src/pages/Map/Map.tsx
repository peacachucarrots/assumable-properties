import {useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import {LoadingWithText} from "../../components/Loading/Loading.tsx";
import {ErrorWithText} from "../../components/Error/Error.tsx";
import styles from "./Map.module.css";

type MapListing = {
    listing_id: number;
    address: string;
    price: number | null;
    loan_type: string;
    mls_status: string | null;
    lat: number | null;
    lon: number | null;
};

const iconUrl       = new URL("leaflet/dist/images/marker-icon.png", import.meta.url).toString();
const iconRetinaUrl = new URL("leaflet/dist/images/marker-icon-2x.png", import.meta.url).toString();
const shadowUrl     = new URL("leaflet/dist/images/marker-shadow.png", import.meta.url).toString();

export const defaultIcon = L.icon({
    iconUrl,
    iconRetinaUrl,
    shadowUrl,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    tooltipAnchor: [16, -28],
    shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = defaultIcon;

function FitBounds({ points }: { points: [number, number][] }) {
    const map = useMap();
    useEffect(() => {
        if (points.length === 0) return;
        const bounds = L.latLngBounds(points);
        map.fitBounds(bounds, { padding: [30, 30] });
    }, [points, map]);
    return null;
}

export default function Map() {
    const [sp] = useSearchParams();
    const selected = sp.getAll("loan_type");

    const qs =
        selected.length === 0
            ? ""
            : "?" + new URLSearchParams(selected.map(v => ["loan_type", v])).toString();

    const { data, isLoading, error } = useQuery<MapListing[]>({
        queryKey: ["listings", "map", selected],
        keepPreviousData: true,
        queryFn: () =>
            fetch(`/api/listings${qs}`, { credentials: "include" }).then(r => {
                if (!r.ok) throw new Error("API error");
                return r.json();
            })
    });

    const points = useMemo(
        () =>
            (data ?? [])
                .filter(d => typeof d.lat === "number" && typeof d.lon === "number")
                .map(d => [d.lat as number, d.lon as number] as [number, number]),
        [data]
    );

    const center: [number, number] = points[0] ?? [39.5, -98.35];
    const hasAny = points.length > 0;

    if (isLoading) return <LoadingWithText text="map" />;
    if (error) return <ErrorWithText text="map" />;

    return (
        <div className={styles.wrapper}>
            <div className={styles.mapCard}>
                <div className={styles.header}>
                    <h1 className={styles.title}>Listings Map</h1>
                    <div className={styles.subtitle}>
                        {selected.length ? `Filtered by ${selected.join(", ")}` : "All loan types"}
                    </div>
                </div>

                <MapContainer
                    center={center}
                    zoom={hasAny ? 8 : 4}
                    className={styles.map}
                    scrollWheelZoom
                    preferCanvas
                >
                    <TileLayer
                        attribution='&copy; OpenStreetMap contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    {hasAny && <FitBounds points={points} />}

                    {(data ?? [])
                        .filter(d => d.lat != null && d.lon != null)
                        .map(d => (
                            <Marker key={d.listing_id} position={[d.lat!, d.lon!]}>
                                <Popup>
                                    <div className={styles.popup}>
                                        <div className={styles.popAddress}>{d.address}</div>
                                        <div className={styles.popLine}>
                                            <span className="muted">Price:</span>{" "}
                                            {d.price ? `$${d.price.toLocaleString()}` : "-"}
                                        </div>
                                        <div className={styles.popLine}>
                                            <span className="muted">Loan:</span> {d.loan_type}
                                            {" ~ "}
                                            <span className="muted">Status:</span> { d.mls_status ?? "-"}
                                        </div>
                                        <Link to={`/listing/${d.listing_id}`} className="btn" style={{ display: "inline-block", marginTop: "0.35rem", color:"white" }}>
                                            View Details
                                        </Link>
                                    </div>
                                </Popup>
                            </Marker>
                        ))}
                </MapContainer>

                {!hasAny && (
                    <div className={styles.empty}>
                        No geocoded listings to show. Add <code>lat</code>/<code>long</code> to your API.
                    </div>
                )}
            </div>
        </div>
    );
}