import { Button, ButtonProps } from "@mantine/core";
import { forwardRef } from "react";


export const ParameterButton = forwardRef<
    HTMLButtonElement,
    ButtonProps
>(function ParameterButton(props, ref) {
    return (
        <Button
            ref={ref}
            variant="gradient"
            gradient={{ from: "indigo", to: "cyan", deg: 45 }}
            size="md"
            radius="lg"
            {...props}
        />
    );
});
