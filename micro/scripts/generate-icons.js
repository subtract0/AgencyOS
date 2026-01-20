/**
 * Icon Generator for Micro
 *
 * This script generates PNG icons from the SVG.
 * Run: node scripts/generate-icons.js
 *
 * Requires: sharp (npm install sharp --save-dev)
 * Or just use an online converter:
 * 1. Open public/icon.svg in browser
 * 2. Use https://cloudconvert.com/svg-to-png
 * 3. Save as icon-192.png and icon-512.png in public/
 */

const fs = require('fs');
const path = require('path');

// Check if sharp is available
try {
  const sharp = require('sharp');

  const svgPath = path.join(__dirname, '../public/icon.svg');
  const svg = fs.readFileSync(svgPath);

  // Generate 192x192
  sharp(svg)
    .resize(192, 192)
    .png()
    .toFile(path.join(__dirname, '../public/icon-192.png'))
    .then(() => console.log('Created icon-192.png'));

  // Generate 512x512
  sharp(svg)
    .resize(512, 512)
    .png()
    .toFile(path.join(__dirname, '../public/icon-512.png'))
    .then(() => console.log('Created icon-512.png'));

} catch (e) {
  console.log('Sharp not installed. Manual icon generation required.');
  console.log('');
  console.log('Option 1: Install sharp and run again');
  console.log('  npm install sharp --save-dev');
  console.log('  node scripts/generate-icons.js');
  console.log('');
  console.log('Option 2: Convert manually');
  console.log('  1. Open public/icon.svg in a browser');
  console.log('  2. Use https://cloudconvert.com/svg-to-png');
  console.log('  3. Save as public/icon-192.png (192x192)');
  console.log('  4. Save as public/icon-512.png (512x512)');
}
