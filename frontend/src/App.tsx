import React, { useState } from 'react';
import StartScreen from './StartScreen';
import MainScreen  from './MainScreen';
import AladinTest from './AladinTest';
import MaskManager from './Technician';
import {Routes, Route, Navigate} from 'react-router-dom';

//different "screens" in the program
enum Screen {
    Start,
    Login,
    Register,
    Main,
    Export
}

export default function Program() {
    //declares a useState function that sets up screen choosing
    const [currentScreen, setCurrentScreen] = useState<Screen>(Screen.Start);

    //sets the screen to its initial value, the Start screen
    const switchScreen = (screen: Screen) => {
        setCurrentScreen(screen);
    };

    //rendering
    return (
        //including different screens
        <Routes>
            <Route index element = {<Navigate to = "/StartScreen" replace />} />
            <Route path = "/StartScreen" element = {<StartScreen />} />
            <Route path = "/MainScreen" element = {<MainScreen />} />
            <Route path = "/Technician" element = {<MaskManager />} />
        </Routes>
    );
}

