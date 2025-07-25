import { createTheme } from '@mantine/core';

export const theme = createTheme({
    fontFamily: 'Cabin, sans-serif',
    colors: {
        brand: [
            '#586072', '#f5f5f5', '#282c34', '#93c5fd',
            '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8',
            '#1e40af', '#1e3a8a',
        ],
    },

    primaryColor: 'brand',
    primaryShade: 5,
    defaultRadius: 'md',

    // default styling for components, still can be tweaked per-component when called
    components: {
        Button: {
            defaultProps: {
                variant: 'filled',
                radius: 'md',
                size: 'md',
            },

            styles: () => ({
                root: {
                    backgroundColor: '#586072',
                    color: '#f5f5f5',
                    padding: '10px 16px',
                    border: '1px solid black',
                    borderRadius: 10,

                    fontSize: 14,
                    fontFamily: 'Cabin, sans-serif',

                    boxShadow: '0 0 12px 4px rgba(0,0,0,.15)',
                },
            }),
        },

        TextInput: {
            styles: () => ({
                input: { textAlign: 'center' },
            })
        },

        Switch: {
            styles: () => ({
                root: {
                    paddingTop: 25,
                },
            })
        },

    }
});