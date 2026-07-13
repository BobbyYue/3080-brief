#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

function usage() {
  console.error("Usage: wrap_svg_as_whiteboard.js <input.svg> <output.xml>");
  process.exit(2);
}

const [, , input, output] = process.argv;
if (!input || !output) usage();

const svg = fs.readFileSync(input, "utf8").trim();
if (!svg.startsWith("<svg")) {
  console.error(`Input does not look like an SVG: ${input}`);
  process.exit(1);
}

const validator = path.join(__dirname, "validate_whiteboard_svg.py");
const validation = spawnSync("python3", [validator, input], { encoding: "utf8" });
if (validation.status !== 0) {
  process.stderr.write(validation.stdout || "");
  process.stderr.write(validation.stderr || "");
  process.exit(validation.status || 1);
}
if (/<\/whiteboard\s*>/i.test(svg)) {
  console.error("SVG must not contain a nested </whiteboard> tag.");
  process.exit(1);
}

fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, `<whiteboard type="svg">\n${svg}\n</whiteboard>\n`);
console.log(output);
