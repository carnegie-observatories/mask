import React from 'react';

interface ButtonProps {
    text: string;
    onClick: () => void;
}

function JS9ControlButton({ text, onClick }: ButtonProps) {
    return (
        <button className = "JS9-control-button" onClick = {onClick}>
            {text}
        </button>
    );
}

export default JS9ControlButton;