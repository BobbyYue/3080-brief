#!/usr/bin/env node
const input = process.argv[2];

if (!input) {
  console.error("Usage: extract_lark_doc_token.js <lark-doc-url-or-token>");
  process.exit(2);
}

const patterns = [
  /\/docx\/([A-Za-z0-9]+)/,
  /\/wiki\/([A-Za-z0-9]+)/,
  /\/docs\/([A-Za-z0-9]+)/,
];

for (const pattern of patterns) {
  const match = input.match(pattern);
  if (match) {
    console.log(match[1]);
    process.exit(0);
  }
}

if (/^[A-Za-z0-9]{8,}$/.test(input)) {
  console.log(input);
  process.exit(0);
}

console.error("Could not extract a Lark doc token.");
process.exit(1);
