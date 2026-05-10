const editor = document.querySelector("#code");
const output = document.querySelector("#output");
const copyButton = document.querySelector("#copy");

const starterCode = `bounty x = 5
say x + 1

dfruit add(a, b):
    return a + b

say add(2, 3)
`;

editor.value = starterCode;
output.textContent = "6\n5";

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(editor.value);
    copyButton.textContent = "Copied";
    setTimeout(() => {
      copyButton.textContent = "Copy code";
    }, 1200);
  } catch (error) {
    output.textContent = "Select the code and copy it manually.";
  }
});
