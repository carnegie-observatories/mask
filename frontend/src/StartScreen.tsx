import React from 'react';
import Button from './Button';
import { useNavigate } from 'react-router-dom';

function StartScreen() {

    const navigate = useNavigate();

    const handleLogin = () => {
        //When Login button is clicked
        console.log("Login button clicked");
    };

    const handleRegister = () => {
        //When Register button is clicked
        console.log("Register button clicked");
    };

    const handleGuest = () => {
        //When Guest button is clicked
        console.log("Guest button clicked");
        navigate('/MainScreen', { replace: true });
    };

    return (
        <div>
            <h1 className = "title">SlitMask Interface</h1>
            <div className="start-screen-container">
                <Button text = "Login"          onClick = {handleLogin} />
                <Button text = "Register"       onClick = {handleRegister} />
                <Button text = "Guest Login"    onClick = {handleGuest} />
            </div>
        </div>
    );
}

export default StartScreen;
