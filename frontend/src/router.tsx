import { createBrowserRouter, Outlet, RouterProvider } from "react-router-dom";
import Home          from "./pages/Home/Home";
import ListingsPage  from "./pages/Listings/ListingsPage/Listings";
import AddListing    from "./pages/Listings/AddListing/AddListing";
import ListingDetail from "./pages/Listings/ListingDetail/ListingDetail";
import Map           from "./pages/Map/Map";
import Navbar        from "./components/Navbar/Navbar.tsx";
import { authLoader } from "./authLoader.ts";

function PrivateLayout() {
    return (
        <>
            <Navbar />
            <Outlet />
        </>
    );
}

export const router = createBrowserRouter([
    // Public
    { path: "/", element: <Home /> },
    // Private
    {
        path: "/",
        element: <PrivateLayout />,
        loader: authLoader,
        children: [
            { path: "/listings", element: <ListingsPage /> },
            { path: "/AddListing", element: <AddListing /> },
            { path: "/listing/:id", element: <ListingDetail /> },
            { path: "/map", element: <Map /> }
        ]
    }
]);

export function AppRouter() {
    return <RouterProvider router={router} />;
}