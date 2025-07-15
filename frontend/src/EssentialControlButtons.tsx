import React from 'react';

interface ButtonProps {
    icon?: React.ReactNode;
    text: string;
    onClick: () => void;
}

function EssentialControlButtons({ icon, text, onClick }: ButtonProps) {
    return (
        <button className = "essential-control-button" onClick = {onClick}>
            <div className = "ecb-icon">{icon}</div>
            <span className = "ecb-label">{text}</span>
        </button>
    );
}

export default EssentialControlButtons;