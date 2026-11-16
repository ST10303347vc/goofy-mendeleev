const sans = ['Inter', 'sans-serif'];
const mono = ['"JetBrains Mono"', 'monospace'];

module.exports = {
    content: ['./frontend/index.html', './frontend/app.js'],
    theme: {
        extend: {
            fontFamily: { sans, jp: sans, mono },
            colors: {
                ink: { DEFAULT: 'rgb(var(--ink-rgb) / <alpha-value>)', soft: 'rgb(var(--soft-rgb) / <alpha-value>)', faint: 'rgb(var(--muted-rgb) / <alpha-value>)' },
                paper: 'rgb(var(--paper-rgb) / <alpha-value>)',
                indigo: 'rgb(var(--indigo-rgb) / <alpha-value>)',
                goldc: 'rgb(var(--gold-rgb) / <alpha-value>)',
                danger: 'rgb(var(--danger-rgb) / <alpha-value>)',
                success: 'rgb(var(--success-rgb) / <alpha-value>)',
                water: 'rgb(var(--water-rgb) / <alpha-value>)',
            },
        },
    },
};
