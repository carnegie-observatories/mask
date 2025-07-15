import React, { useEffect } from "react";

declare global {
    interface Window { JS9: any; }
}

interface JS9ViewerProps {
    /** URL of the FITS file */
    fitsUrl: string;
    /** Optional JS9 options */
    options?: { colormap?: string };
}

export default function JS9Viewer({fitsUrl, options,}: JS9ViewerProps) {
    const id = "js9";
    useEffect(() => {
        if (!window.JS9) {
            console.error("JS9 never loaded.");
            return;
        }
        // This will scan the DOM for any <div class = "JS9" data-url="...">
        window.JS9.init();

        window.JS9.Load(fitsUrl, { width:  "100%", height: "100%",},  () => {
            console.log("JS9 loaded FITS");
        });

    }, [fitsUrl, options]);

    //rendering JS9
    return (
        <div
            id = {id}
            className = "JS9"
            style = {{width: "100%", height: "100%", backgroundColor: "#000",}}
        />
    );
}
