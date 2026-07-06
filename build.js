const fs = require('fs');
const path = require('path');

function minifyCSS(css) {
    return css
        .replace(/\/\*[\s\S]*?\*\//g, '') // remove comments
        .replace(/\s+/g, ' ')             // collapse multiple whitespaces
        .replace(/\s*([{};,])\s*/g, '$1') // remove space around braces, colons, semi-colons, commas
        .trim();
}

function minifyJS(js) {
    return js
        .replace(/\/\*[\s\S]*?\*\//g, '') // remove block comments
        .replace(/\/\/.*$/gm, '')         // remove inline comments
        .replace(/\s+/g, ' ')             // collapse whitespace
        .replace(/\s*([=+\-*/%&|!<>;,{}()\[\]])\s*/g, '$1') // remove space around operators and braces
        .trim();
}

const cssSrc = path.join(__dirname, 'src', 'citizenbenefits', 'static', 'assets', 'css', 'styles.css');
const cssDist = path.join(__dirname, 'src', 'citizenbenefits', 'static', 'assets', 'css', 'styles.min.css');
const jsSrc = path.join(__dirname, 'src', 'citizenbenefits', 'static', 'assets', 'js', 'styles.js');
const jsDist = path.join(__dirname, 'src', 'citizenbenefits', 'static', 'assets', 'js', 'styles.min.js');

try {
    const rawCss = fs.readFileSync(cssSrc, 'utf8');
    const minCss = minifyCSS(rawCss);
    fs.writeFileSync(cssDist, minCss, 'utf8');
    console.log('Minified CSS written to styles.min.css');
} catch (e) {
    console.error('Failed to minify CSS:', e);
}

try {
    const rawJs = fs.readFileSync(jsSrc, 'utf8');
    const minJs = minifyJS(rawJs);
    fs.writeFileSync(jsDist, minJs, 'utf8');
    console.log('Minified JS written to styles.min.js');
} catch (e) {
    console.error('Failed to minify JS:', e);
}
