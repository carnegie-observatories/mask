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

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
