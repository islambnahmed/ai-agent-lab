import test from "node:test";
import assert from "node:assert/strict";

// Regression for network responses that arrive after the user has selected a local data source.
function setup() {
  const elements = new Map();
  function el(id) {
    if (!elements.has(id)) elements.set(id, {
      textContent: "", innerHTML: "", className: "", disabled: false, handlers: {},
      classList: { toggle() {} },
      addEventListener(event, handler) { this.handlers[event] = handler; }
    });
    return elements.get(id);
  }
  const pending = [];
  const previous = { document: globalThis.document, fetch: globalThis.fetch };
  globalThis.document = { getElementById: el, querySelectorAll: () => [] };
  globalThis.fetch = url => new Promise(resolve => pending.push({ url, resolve }));
  function restore() {
    globalThis.document = previous.document;
    globalThis.fetch = previous.fetch;
  }
  return { el, pending, restore };
}

function fixtures() {
  const now = Date.now();
  return {
    history: {
      metal: "XAU", grain: "daily", unit: "USD per troy ounce",
      points: Array.from({ length: 360 }, (_, i) => ({
        t: new Date(now - (359 - i) * 86400000).toISOString(), price: 4100 + i
      }))
    },
    spot: {
      unit: "USD per troy ounce", updated: new Date(now - 60000).toISOString(),
      metals: [{ symbol: "XAU", ask: 4500, bid: 4490 }]
    }
  };
}
async function finishPending(pending) {
  const { history, spot } = fixtures();
  assert.equal(pending.length, 2, "both provider requests must still be in flight");
  for (const p of pending) p.resolve({
    ok: true, json: async () => p.url.includes("history") ? history : spot
  });
  for (let i = 0; i < 12; i++) await Promise.resolve();
  await new Promise(resolve => setImmediate(resolve));
}

test("DEMO choice survives a late response from earlier provider refresh", async () => {
  const { el, pending, restore } = setup();
  try {
    await import("../app_verified.mjs?race=demo");
    el("demo").handlers.click();
    assert.match(el("status").textContent, /DEMO/);
    await finishPending(pending);
    assert.match(el("status").textContent, /DEMO/);
    assert.match(el("source").textContent, /DEMO/);
    assert.equal(el("ask").textContent, "—");
  } finally { restore(); }
});

test("CSV choice survives a late response from earlier provider refresh", async () => {
  const { el, pending, restore } = setup();
  try {
    await import("../app_verified.mjs?race=csv");
    const start = Date.now() - 400 * 86400000;
    const rows = Array.from({ length: 360 }, (_, i) => {
      const day = new Date(start + i * 86400000).toISOString().slice(0, 10);
      return `${day},${4100 + i}`;
    });
    const file = { name: "local.csv", text: async () => "date,price\n" + rows.join("\n") };
    await el("csv").handlers.change({ target: { files: [file], value: "local.csv" } });
    assert.match(el("status").textContent, /CSV/);
    await finishPending(pending);
    assert.match(el("status").textContent, /CSV/);
    assert.match(el("source").textContent, /local\.csv/);
    assert.equal(el("ask").textContent, "—");
  } finally { restore(); }
});
