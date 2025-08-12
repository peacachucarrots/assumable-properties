import {createBrowserRouter, Outlet, RouterProvider} from "react-router-dom";
import Home          from "./pages/Home/Home";
import ListingsPage  from "./pages/Listings/ListingsPage/Listings";
import AddListing    from "./pages/Listings/AddListing/AddListing";
import ListingDetail from "./pages/Listings/ListingDetail/ListingDetail";
import Map           from "./pages/Map/Map";
import Navbar        from "./components/Navbar/Navbar.tsx";

import Test from "./pages/Test.tsx";

export const router = createBrowserRouter([
    {
        path: "/",
        element: <AppLayout />,
        children: [
            { index: true, element: <Home /> },
            { path: "/test", element: <Test /> },
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

function AppLayout() {
    return (
        <>
            <Navbar />
            <Outlet />
        </>
    );
}