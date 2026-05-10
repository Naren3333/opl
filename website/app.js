const editor = document.querySelector("#code");
const output = document.querySelector("#output");
const runButton = document.querySelector("#run");

const starterCode = `import math

fn make_counter() {
    let n = 0

    fn next() {
        n = n + 1
        return n
    }

    return next
}

let counter = make_counter()
print(counter())
print(counter())
print(math.sqrt(25))
`;

editor.value = starterCode;
output.textContent = "Ready.";

async function runCode() {
  runButton.disabled = true;
  output.classList.remove("error");
  output.textContent = "Running...";

  try {
    const response = await fetch("/run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ code: editor.value })
    });

    const result = await response.json();

    if (!result.ok) {
      output.classList.add("error");
    }

    output.textContent = result.output || "(no output)";
  } catch (error) {
    output.classList.add("error");
    output.textContent = [
      "Playground server is not running.",
      "",
      "Start it with:",
      "python website/playground_server.py --port 8787"
    ].join("\n");
  } finally {
    runButton.disabled = false;
  }
}

runButton.addEventListener("click", runCode);
