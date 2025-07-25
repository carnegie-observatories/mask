import React, { useEffect } from "react";

declare global {
    interface Window {
        JS9: any;
        ExitStatus?: unknown;
        __astroLoaded?: boolean;
    }
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
        (async () => {
            if (!window.JS9) {
                console.error('JS9 never loaded.');
                return;
            }

            // initialize
            window.JS9.init();

            // load
            window.JS9.Load(fitsUrl, { width: '100%', height: '100%' }, () => {
                console.log('JS9 loaded: ', fitsUrl);
            });

        })();

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