import React from 'react';

interface ButtonProps {
    text: string;
    onClick: () => void;
}

function StartButton({ text, onClick }: ButtonProps) {
    return (
        <button className = "primaryButton" onClick = {onClick}>
            {text}
        </button>
    );
}

export default StartButton;
