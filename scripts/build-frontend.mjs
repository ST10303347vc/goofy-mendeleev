import { execFileSync } from 'node:child_process';
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const out = join(root, 'frontend/assets');
const modules = join(root, 'node_modules');
mkdirSync(out, { recursive: true });

execFileSync(process.execPath, [
    join(modules, 'tailwindcss/lib/cli.js'), '--config', 'scripts/tailwind.config.cjs',
    '--output', 'frontend/assets/tailwind.css', '--minify',
], { cwd: root, stdio: 'inherit' });

copyFileSync(join(modules, 'vue/dist/vue.global.prod.js'), join(out, 'vue.js'));
copyFileSync(join(modules, 'vue/LICENSE'), join(out, 'vue-LICENSE.txt'));
const phosphor = join(modules, '@phosphor-icons/web');
const iconStyles = [];
for (const [weight, font] of [['light', 'Phosphor-Light'], ['thin', 'Phosphor-Thin']]) {
    const source = join(phosphor, 'src', weight);
    copyFileSync(join(source, `${font}.woff2`), join(out, `${font}.woff2`));
    iconStyles.push(readFileSync(join(source, 'style.css'), 'utf8')
        .replace(/src:[^;]+;/, `src: url("./${font}.woff2") format("woff2");`));
}
writeFileSync(join(out, 'icons.css'), iconStyles.join('\n'));
copyFileSync(join(phosphor, 'LICENSE'), join(out, 'phosphor-LICENSE.txt'));
copyFileSync(join(modules, 'tailwindcss/LICENSE'), join(out, 'tailwind-LICENSE.txt'));

const fonts = [];
for (const [family, weights] of [['inter', [300, 400, 500, 600]], ['jetbrains-mono', [400, 500]]]) {
    const source = join(modules, '@fontsource', family);
    for (const weight of weights) {
        const css = readFileSync(join(source, `${weight}.css`), 'utf8');
        fonts.push(css.replace(/url\(\.\/files\/([^()]+\.woff2)\) format\('woff2'\), url\([^)]+\) format\('woff'\)/g, (_, file) => {
            copyFileSync(join(source, 'files', file), join(out, file));
            return `url(./${file}) format('woff2')`;
        }));
    }
    copyFileSync(join(source, 'LICENSE'), join(out, `${family}-LICENSE.txt`));
}
writeFileSync(join(out, 'fonts.css'), fonts.join('\n'));
