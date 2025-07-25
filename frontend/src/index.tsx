import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import reportWebVitals from './reportWebVitals';
import './index.css';
import {MantineProvider} from "@mantine/core";
import {theme} from "./theme";


// stopping error popups
if (typeof window !== "undefined") {
    window.addEventListener("error", (ev) => {
        // ↓ match the exact text that comes from astroemw.js duplicates
        if (ev.message?.includes("ExitStatus has already been declared")) {
            console.warn("Silenced duplicate ExitStatus error");
            ev.preventDefault();    // stop the error bubbling
        }
    });

    window.addEventListener("unhandledrejection", (ev) => {
        // Some browsers surface the same duplicate declaration as a rejected promise
        if (
            typeof ev.reason?.message === "string" &&
            ev.reason.message.includes("ExitStatus has already been declared")
        ) {
            console.warn("Silenced duplicate ExitStatus rejection");
            ev.preventDefault();
        }
    });
}



const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);


root.render(
    <BrowserRouter>
        <MantineProvider defaultColorScheme="dark" theme={theme}>
            <App />
        </MantineProvider>
    </BrowserRouter>
);

reportWebVitals();


// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
