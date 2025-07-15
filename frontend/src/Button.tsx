import React from 'react';

interface ButtonProps {
    text: string;
    onClick: () => void;
}

function Button({ text, onClick }: ButtonProps) {
    return (
        <button className = "primaryButton" onClick = {onClick}>
            {text}
        </button>
    );
}

export default Button;
