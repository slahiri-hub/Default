(() => {
  "use strict";

  const inputEl = document.getElementById("input-text");
  const outputEl = document.getElementById("output-text");
  const inputCountEl = document.getElementById("input-count");
  const noteEl = document.getElementById("note");
  const alternatesEl = document.getElementById("alternates");
  const alternatesListEl = document.getElementById("alternates-list");
  const langLeftBtn = document.getElementById("lang-left");
  const langRightBtn = document.getElementById("lang-right");
  const swapBtn = document.getElementById("swap-btn");
  const autoDetectEl = document.getElementById("auto-detect");
  const clearBtn = document.getElementById("clear-btn");
  const copyBtn = document.getElementById("copy-btn");

  const MAX_CHARS = 2000;
  const DEBOUNCE_MS = 250;

  // "auto" lets the server pick a direction per request; otherwise it's
  // pinned to whichever language button the user last clicked (or what the
  // swap button last set).
  let direction = "auto";
  let lastUsedDirection = "en-tp";
  let debounceTimer = null;
  let requestSeq = 0;

  function setLangButtons(activeDirection) {
    langLeftBtn.setAttribute("aria-pressed", String(activeDirection === "en-tp"));
    langRightBtn.setAttribute("aria-pressed", String(activeDirection === "tp-en"));
  }

  function renderOutput(text) {
    outputEl.textContent = "";
    if (!text) {
      const span = document.createElement("span");
      span.className = "placeholder";
      span.textContent = "Translation will appear here.";
      outputEl.appendChild(span);
      return;
    }
    // Render `⟨word?⟩` unknown-vocabulary placeholders as a styled span
    // without ever interpreting any part of the string as HTML.
    const re = /⟨[^⟩]*⟩/g;
    let last = 0;
    let match;
    while ((match = re.exec(text)) !== null) {
      if (match.index > last) {
        outputEl.appendChild(document.createTextNode(text.slice(last, match.index)));
      }
      const span = document.createElement("span");
      span.className = "unknown";
      span.textContent = match[0];
      outputEl.appendChild(span);
      last = match.index + match[0].length;
    }
    if (last < text.length) {
      outputEl.appendChild(document.createTextNode(text.slice(last)));
    }
  }

  function renderNote(note) {
    if (!note) {
      noteEl.hidden = true;
      noteEl.textContent = "";
      noteEl.classList.remove("swap-suggestion");
      noteEl.onclick = null;
      return;
    }
    noteEl.hidden = false;
    noteEl.textContent = note;
    if (note.includes("Swap directions")) {
      noteEl.classList.add("swap-suggestion");
      noteEl.title = "Click to swap languages";
      noteEl.onclick = doSwap;
    } else {
      noteEl.classList.remove("swap-suggestion");
      noteEl.onclick = null;
    }
  }

  function renderAlternates(readings) {
    alternatesListEl.textContent = "";
    if (readings.length <= 1) {
      alternatesEl.hidden = true;
      return;
    }
    alternatesEl.hidden = false;
    readings.slice(1).forEach((reading) => {
      const li = document.createElement("li");
      li.textContent = reading;
      li.tabIndex = 0;
      li.addEventListener("click", () => renderOutput(reading));
      alternatesListEl.appendChild(li);
    });
  }

  async function translate() {
    const text = inputEl.value;
    inputCountEl.textContent = String(text.length);

    if (!text.trim()) {
      renderOutput("");
      renderNote(null);
      renderAlternates([]);
      return;
    }

    const seq = ++requestSeq;
    try {
      const resp = await fetch("/api/translate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, direction }),
      });
      const data = await resp.json();
      if (seq !== requestSeq) return; // a newer request has since started

      lastUsedDirection = data.direction_used || lastUsedDirection;
      if (direction === "auto") {
        setLangButtons(lastUsedDirection);
      }
      renderOutput(data.readings && data.readings.length ? data.readings[0] : "");
      renderNote(data.note);
      renderAlternates(data.readings || []);
    } catch (err) {
      if (seq !== requestSeq) return;
      renderOutput("");
      renderNote("Translation request failed. Please try again.");
      renderAlternates([]);
    }
  }

  function scheduleTranslate() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(translate, DEBOUNCE_MS);
  }

  function pinDirection(newDirection) {
    direction = newDirection;
    lastUsedDirection = newDirection;
    autoDetectEl.checked = false;
    setLangButtons(newDirection);
    scheduleTranslate();
  }

  function doSwap() {
    const newDirection = lastUsedDirection === "en-tp" ? "tp-en" : "en-tp";
    const hasRealOutput = !outputEl.querySelector(".placeholder");
    inputEl.value = hasRealOutput ? outputEl.textContent.trim() : "";
    pinDirection(newDirection);
  }

  langLeftBtn.addEventListener("click", () => pinDirection("en-tp"));
  langRightBtn.addEventListener("click", () => pinDirection("tp-en"));
  swapBtn.addEventListener("click", doSwap);

  autoDetectEl.addEventListener("change", () => {
    direction = autoDetectEl.checked ? "auto" : lastUsedDirection;
    if (!autoDetectEl.checked) setLangButtons(lastUsedDirection);
    scheduleTranslate();
  });

  inputEl.addEventListener("input", () => {
    if (inputEl.value.length > MAX_CHARS) {
      inputEl.value = inputEl.value.slice(0, MAX_CHARS);
    }
    inputCountEl.textContent = String(inputEl.value.length);
    scheduleTranslate();
  });

  clearBtn.addEventListener("click", () => {
    inputEl.value = "";
    inputEl.focus();
    translate();
  });

  copyBtn.addEventListener("click", async () => {
    const text = outputEl.textContent;
    if (!text || outputEl.querySelector(".placeholder")) return;
    try {
      await navigator.clipboard.writeText(text);
      const original = copyBtn.textContent;
      copyBtn.textContent = "Copied!";
      setTimeout(() => (copyBtn.textContent = original), 1200);
    } catch (err) {
      // Clipboard API unavailable (e.g. insecure context) -- ignore silently.
    }
  });

  setLangButtons("en-tp");
  renderOutput("");
})();
