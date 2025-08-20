import { useEffect, useMemo, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import type { Marker as LeafletMarker } from "leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import {LoadingWithText} from "../../components/Loading/Loading.tsx";
import {ErrorWithText} from "../../components/Error/Error.tsx";
import styles from "./Map.module.css";
import {LoanBadge, StatusBadge} from "../../components/Badges/Badges.tsx";

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

const isActive = (s: string | null | undefined) =>
  !!s && s.trim().toLowerCase().startsWith("active");

function FitBounds({ points }: { points: [number, number][] }) {
    const map = useMap();
    useEffect(() => {
        if (points.length === 0) return;
        const bounds = L.latLngBounds(points);
        map.fitBounds(bounds, { padding: [30, 30] });
    }, [points, map]);
    return null;
}

export default function ListingsMap() {
    const [sp] = useSearchParams();
    const selected = sp.getAll("loan_type");
    const focusId = sp.get("focus");

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

    const activeGeocoded = useMemo(
        () =>
            (data ?? []).filter(
                (d) => isActive(d.mls_status) && typeof d.lat === "number" && typeof d.lon === "number"
            ),
        [data]
    );

    const focus = useMemo(
        () =>
            (data ?? []).find(
                (d) =>
                    focusId && String(d.listing_id) === String(focusId) && d.lat != null && d.lon != null
            ) || null,
        [data, focusId]
    );

    const displayListings = useMemo(() => {
        if (!focus) return activeGeocoded;
        const map = new Map<number, MapListing>();
        for (const d of activeGeocoded) map.set(d.listing_id, d);
        map.set(focus.listing_id, focus);
        return Array.from(map.values());
    }, [activeGeocoded, focus]);

    const points = useMemo<[number, number][]>(
        () => displayListings.map((d) => [d.lat as number, d.lon as number]),
        [displayListings]
    );

    const hasAny = points.length > 0;
    const center: [number, number] = focus
        ? [focus.lat as number, focus.lon as number]
        : points[0] ?? [39.5, -98.35];
    const zoom = focus ? 13 : hasAny ? 8 : 4;

    const focusMarkerRef = useRef<LeafletMarker | null>(null);

    useEffect(() => {
        if (focus) {
            const t = setTimeout(() => focusMarkerRef.current?.openPopup(), 50);
            return () => clearTimeout(t);
        }
    }, [focus?.listing_id]);

    if (isLoading) return <LoadingWithText text="map" />;
    if (error) return <ErrorWithText error="Error loading map" />;

    return (
        <div className={styles.wrapper}>
            <div className={styles.mapCard}>
                <div className={styles.header}>
                    <h1 className={styles.title}>Listings Map</h1>
                    <div className={styles.subtitle}>
                        {focus ? "Focusing selected listing" : "Active only"}
                    </div>
                </div>

                <MapContainer
                    center={center}
                    zoom={zoom}
                    className={styles.map}
                    scrollWheelZoom
                    preferCanvas
                >
                    <TileLayer
                        attribution='&copy; OpenStreetMap contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    {!focus && hasAny && <FitBounds points={points} />}

                    {displayListings.map((d) => (
                        <Marker
                            key={d.listing_id}
                            position={[d.lat!, d.lon!]}
                            ref={d.listing_id === focus?.listing_id ? focusMarkerRef : undefined}
                        >
                            <Popup>
                                <div className={styles.popup}>
                                    <div className={styles.popAddress}>{d.address}</div>
                                    <div className={styles.popLine}>
                                        <span className="muted">Price:</span>{" "}
                                        {d.price ? `$${d.price.toLocaleString()}` : "-"}
                                    </div>
                                    <div className={styles.popLine}>
                                        <span className="muted">Loan:</span> <LoanBadge value={d.loan_type} />
                                        {" · "}
                                        <span className="muted">Status:</span> <StatusBadge value={d.mls_status} />
                                    </div>
                                    <Link
                                        to={`/listing/${d.listing_id}`}
                                        className="btn"
                                        style={{ display: "inline-block", marginTop: "0.35rem", color:"white" }}
                                    >
                                        View Details
                                    </Link>
                                </div>
                            </Popup>
                        </Marker>
                        ))}
                </MapContainer>

                {!hasAny && (
                    <div className={styles.empty}>
                        No <strong>active</strong> geocoded listings to show.
                    </div>
                )}
            </div>
        </div>
    );
}