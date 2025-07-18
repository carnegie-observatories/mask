import React, { useEffect, useState, useRef } from 'react';
import {useNavigate} from "react-router-dom";


//icons. doesn't work properly, not recognized as JSX components. will fix later
// import { FiCornerUpLeft, FiCornerUpRight, FiFileText, FiSave, FiPower} from 'react-icons/fi';
// import { RiResetLeftLine } from "react-icons/ri";
// import { MdLogout } from "react-icons/md";


import EssentialControlButtons from './EssentialControlButtons';
import JS9ControlButton from "./JS9ControlButton";
import JS9Viewer from "./JS9Viewer";
import {ParameterButton} from "./components/ParameterButton"
import { FileButton, Button } from "@mantine/core";


// import { stopReportingRuntimeErrors } from "react-error-overlay";
// stopReportingRuntimeErrors();

// preventing unimportant errors from popping up
function safeLoadAstroEmw() {
    // only attach astroemw.js once per browser tab (CAUSES THE DUMB EXITSTATUS ERRORS)
    if (window.__astroLoaded) return;
    window.__astroLoaded = true;

    try {
        // @ts-ignore - no types for astroemw
        import(/* webpackIgnore: true */ '/JS9/astroemw.js');
        (window as any).__astroEMWLoaded = true;
    } catch {
        /* ignore duplicate-load “ExitStatus” noise */
    }
}


function MainScreen() {
    const navigate = useNavigate();
    const exampleFits = "casa.fits";


    // upload object file logic
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [apiResponse, setApiResponse] = useState<any | null>(null);
    const [loading, setLoading] = useState(false);
    const [error,   setError]   = useState<string | null>(null);


    // when user uploads object file, sends to API and awaits return
    // @ts-ignore
    async function uploadObjectFiles(files: File[],  listName: string) {
        console.log("Upload initiated for: ", files);
        if (!files.length) return;
        setLoading(true);
        setError(null);

        try {
            const form = new FormData();
            form.append('file', files[0]);
            form.append("user_id", "tester");
            form.append("list_name", listName);

            // actually sending the request
            const maskData = await fetch('/api/objects/upload/', {
                method: 'POST',
                body: form,
            });

            if (!maskData.ok) {
                throw new Error(`Server responded ${maskData.status}`);
            }

            const apiResponse = await maskData.json();
            console.log('API response:', apiResponse);
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'Upload failed');
        } finally {
            setLoading(false);
        }
    }

    // adds files to list
    const handleObjectFiles = (files: File | File[] | null): void => {
        if (!files) return;
        const fileArray = Array.isArray(files) ? files : [files];
        setSelectedFiles((prev) => [...prev, ...fileArray]);
    }




    // escape key function
    useEffect(() => {
        const onEsc = (e: KeyboardEvent) => {
            //Goes back to start if Escape key is pressed
            if (e.key === 'Escape') {
                navigate('/', { replace: true });
            }
        };
        window.addEventListener('keydown', onEsc);
        return () => window.removeEventListener('keydown', onEsc);
    }, [navigate]);



    // essential control button handlers
    const handleGenExport = () => {
        //When Generate and Export button is clicked
        console.log("GenEx button clicked");
    };

    const handleUndo= () => {
        //When Undo button is clicked
        console.log("Undo button clicked");
    }

    const handleRedo= () => {
        //When Redo button is clicked
        console.log("Redo button clicked");
    }

    const handleLogOut = () => {
        //When log out button is clicked
        console.log("Logout button clicked");
        navigate('/', { replace: true });
    }

    const handleReset = () => {
        //when reset button is clicked
        console.log("Reset button clicked");
    }

    const handleQuit = () => {
        //when user quits
        console.log("Quit button clicked");
        window.open('', '_self');
        window.close();
    }

    const handleParameterHistory = () => {
        console.log("Parameter History button clicked");
    }


    // loading a FITS file
    const fileRef = useRef<HTMLInputElement>(null);

    const handleLoad = () => {
        console.log("Load button clicked");
        fileRef.current?.click();
    }

    const handleLoadFile = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            console.log("Loading: ", file.name);
            window.JS9.Load(file);
        }
    }



    // handlers for zooming
    const handleZoomIn = () => {
        //when zoom in button is clicked
        console.log("Zoom In button clicked");
        window.JS9.SetZoom("in");
    }

    const handleZoomOut = () => {
        console.log("Zoom Out button clicked");
        window.JS9.SetZoom("out");
    }

    const handleZoomReset = () => {
        window.JS9.SetZoom("1");
    }




    // handlers for drawing regions
    const handleDrawCircle = () => {
        window.JS9.AddRegions("circle",{color:"cyan"})
    }

    const handleDrawDonut = () => {
        window.JS9.AddRegions("annulus", {color: "cyan"})
    }

    const handleDrawRectangle = () => {
        window.JS9.AddRegions("box", {color: "cyan"});
    }

    const handleDrawOval = () => {
        window.JS9.AddRegions("ellipse", {color: "cyan"});
    }

    const handleDrawLine = () => {
        window.JS9.AddRegions("cross", {color: "cyan"});
    }

    const handleDrawTriangle = () => {
        window.JS9.AddRegions("polygon", {color: "cyan"});
    }

    const handleAddText = () => {
        window.JS9.AddRegions("text", {color: "cyan"});
    }


    // calling the error prevention
    useEffect(() => {
        if ((window as any).JS9) {
            safeLoadAstroEmw();
        }
    }, []);


    // handler for submit button (for object file upload)
    const handleSubmitFiles = () => {
        console.log("Submit Files button clicked");
        let objectFileTitle = prompt("Title: ");
        if (!objectFileTitle) return;
        uploadObjectFiles(selectedFiles, objectFileTitle);
    }


    //rendering
    return (
        <div className="main-screen">

            {/* Parameter controls and inputs */}
            <aside className="param-controls">
                <h3>Parameters</h3>

                {/*upload object files button*/}
                {/*@ts-ignore*/}
                <FileButton onChange={handleObjectFiles} accept=".csv,.obj,.json" multiple>
                    {(props) => (
                        <ParameterButton {...props}>Upload Object Files</ParameterButton>
                    )}
                </FileButton>

                {/*listing the objects*/}
                {/*@ts-ignore*/}
                {selectedFiles.length > 0 && (
                    <ul className="uploaded-files">
                        {/*listing the files*/}
                        {selectedFiles.map((file) => (
                            <li key={file.name}>{file.name}</li>
                        ))}

                        {/*submit button*/}
                        <Button onClick={handleSubmitFiles}>Submit</Button>

                        {error && <li style={{ color: 'red' }}>{error}</li>}
                        {apiResponse && <li style={{ color: 'lime' }}>✓ received</li>}

                    </ul>
                )}


            </aside>

            {/* → Where the JS9 panel goes */}
            <div className="preview-area">
                <JS9Viewer fitsUrl={exampleFits} options={{colormap: "cool"}}/>
            </div>


            {/* → fixed-width sidebar for essential controls */}
            <aside className="sidebar">
                {/*<h2>Essential Controls</h2>*/}
                <EssentialControlButtons text="Load" onClick={handleLoad}/>
                <EssentialControlButtons text="Reset Parameters" onClick={handleReset}/>
                <EssentialControlButtons text="Undo" onClick={handleUndo}/>
                <EssentialControlButtons text="Redo" onClick={handleRedo}/>
                <EssentialControlButtons text="Parameter History" onClick={handleParameterHistory}/>
                <EssentialControlButtons text="Generate & Export" onClick={handleGenExport}/>
                <EssentialControlButtons text="Log Out" onClick={handleLogOut}/>
                <EssentialControlButtons text="Quit Application" onClick={handleQuit}/>

                {/*accepting FIT files for loading*/}
                <input
                    type="file"
                    accept=".fits, .fit, .fts"
                    ref={fileRef}
                    onChange={handleLoadFile}
                    style={{ display: "none" }}
                />

            </aside>

            {/* → area below the JS9 panel */}
            <div className="bottom-area">
                {/*<h4>photo settings maybe??</h4>*/}

                {/*default menu bar stuff*/}
                {/*<div className="JS9Menubar"></div>*/}
                {/*<div className="JS9Toolbar"></div>*/}
                {/*<div className="JS9"></div>*/}

                <div className="first-row-controls">
                    <JS9ControlButton text="Zoom In" onClick={handleZoomIn}/>
                    <JS9ControlButton text="Zoom Out" onClick={handleZoomOut}/>
                    <JS9ControlButton text="Reset Zoom" onClick={handleZoomReset}/>
                </div>

                <div className="second-row-controls">
                    <JS9ControlButton text="Draw Donut" onClick={handleDrawDonut}/>
                    <JS9ControlButton text="Draw Circle" onClick={handleDrawCircle}/>
                    <JS9ControlButton text="Draw Rectangle" onClick={handleDrawRectangle}/>
                    <JS9ControlButton text="Draw Oval" onClick={handleDrawOval}/>
                    <JS9ControlButton text="Draw Line" onClick={handleDrawLine}/>
                    <JS9ControlButton text="Draw Triangle" onClick={handleDrawTriangle}/>
                    <JS9ControlButton text="Add Text" onClick={handleAddText}/>
                </div>

                {/*if (drawMenu && toggleCounter % 2 === 1) {*/}
                {/*    <>*/}
                {/*        <div className="JS9Menubar"></div>*/}
                {/*        <div className="JS9Toolbar"></div>*/}
                {/*        <div className="JS9"></div>*/}
                {/*    </>*/}
                {/*}*/}

            </div>

        </div>
    );
}

export default MainScreen;