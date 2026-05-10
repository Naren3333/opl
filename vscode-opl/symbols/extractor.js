const fs = require("fs/promises");

const IDENTIFIER = "[A-Za-z_][A-Za-z0-9_]*";

function emptySymbols() {
  return {
    functions: [],
    models: [],
    variables: []
  };
}

function stripCommentsAndStrings(source) {
  let result = "";
  let inString = false;
  let quote = "";
  let inLineComment = false;

  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];
    const next = source[i + 1];

    if (inLineComment) {
      if (char === "\n") {
        inLineComment = false;
        result += char;
      } else {
        result += " ";
      }
      continue;
    }

    if (inString) {
      if (char === "\\" && next) {
        result += "  ";
        i += 1;
        continue;
      }

      if (char === quote) {
        inString = false;
        quote = "";
      }

      result += char === "\n" ? "\n" : " ";
      continue;
    }

    if (char === "/" && next === "/") {
      inLineComment = true;
      result += "  ";
      i += 1;
      continue;
    }

    if (char === "\"" || char === "'") {
      inString = true;
      quote = char;
      result += " ";
      continue;
    }

    result += char;
  }

  return result;
}

function collectMatches(source, pattern) {
  const matches = new Set();
  let match = pattern.exec(source);

  while (match) {
    matches.add(match[1]);
    match = pattern.exec(source);
  }

  return [...matches].sort();
}

function extractSymbolsFromText(source) {
  const cleanSource = stripCommentsAndStrings(source);

  return {
    functions: collectMatches(
      cleanSource,
      new RegExp(`\\b(?:fn|dfruit)\\s+(${IDENTIFIER})\\s*\\(`, "g")
    ),
    models: collectMatches(
      cleanSource,
      new RegExp(`\\bmodel\\s+(${IDENTIFIER})\\b`, "g")
    ),
    variables: collectMatches(
      cleanSource,
      new RegExp(`\\b(?:let|bounty)\\s+(${IDENTIFIER})\\b`, "g")
    )
  };
}

async function extractSymbolsFromFile(filePath) {
  const source = await fs.readFile(filePath, "utf8");
  return extractSymbolsFromText(source);
}

function mergeSymbolTables(tables) {
  const merged = emptySymbols();

  for (const table of tables) {
    for (const kind of Object.keys(merged)) {
      for (const symbol of table[kind] || []) {
        if (!merged[kind].includes(symbol)) {
          merged[kind].push(symbol);
        }
      }
    }
  }

  for (const kind of Object.keys(merged)) {
    merged[kind].sort();
  }

  return merged;
}

module.exports = {
  emptySymbols,
  extractSymbolsFromFile,
  extractSymbolsFromText,
  mergeSymbolTables
};
