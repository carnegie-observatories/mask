import React from 'react';

interface ButtonProps {
    text: string;
    onClick: () => void;
}

function PreviewControlButton({ text, onClick }: ButtonProps) {
    return (
        <button className = "preview-control-button" onClick = {onClick}>
            {text}
        </button>
    );
}

export default PreviewControlButton;