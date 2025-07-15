// src/react-icons.d.ts
import * as React from 'react';

// FC guarantees a return type of ReactElement | null
type IconFC = React.FunctionComponent<React.SVGProps<SVGSVGElement>>;

declare module 'react-icons/fi' {
    export const FiCornerUpLeft:  IconFC;
    export const FiCornerUpRight: IconFC;
    export const FiFileText:      IconFC;
    export const FiSave:          IconFC;
    export const FiPower:         IconFC;
}

declare module 'react-icons/ri' {
    export const RiResetLeftLine: IconFC;
}

declare module 'react-icons/md' {
    export const MdLogout:        IconFC;
}
