import { Button } from '@mantine/core';
import React from 'react';


interface ButtonProps {
    icon?: React.ReactNode;
    onClick: () => void;
    text: string;
}

function EssentialControlButtons({ icon, text, onClick }: ButtonProps) {
    return (
        <Button onClick={onClick} className="ecb" fullWidth>
            {/* stack icon above label */}
            <div className="ecb-stack">
                {icon && <span className="ecb-icon">{icon}</span>}
                <span className="ecb-label">{text}</span>
            </div>
        </Button>
    );
}

export default EssentialControlButtons;