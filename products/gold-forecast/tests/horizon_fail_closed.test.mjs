import test from "node:test";
import assert from "node:assert/strict";

// Regression: changing from a supported horizon to one with insufficient
// validation samples must remove all previously displayed forecast values.
test("horizon switch fails closed, then recovers when a valid horizon is chosen", async () => {
  const elements = new Map();
  const element = id => {
    if (!elements.has(id)) elements.set(id, {
      textContent: "", innerHTML: "", className: "", disabled: false,
      handlers: {}, classList: { toggle() {} },
      addEventListener(type, fn) { this.handlers[type] = fn; }
    });
    return elements.get(id);
  };
  const buttons = [1, 7, 30].map(h => ({
    dataset: { h: String(h) }, handlers: {}, classList: { toggle() {} },
    addEventListener(type, fn) { this.handlers[type] = fn; }
  }));
  const oldDocument = globalThis.document;
  const oldFetch = globalThis.fetch;
  const now = Date.now();
  const history = {
    metal: "XAU", grain: "daily", unit: "USD per troy ounce",
    points: Array.from({ length: 165 }, (_, i) => ({
      t: new Date(now - (164 - i) * 86400000).toISOString(),
      price: 4100 + i
    }))
  };
  const spot = {
    unit: "USD per troy ounce", updated: new Date(now - 60000).toISOString(),
    metals: [{ symbol: "XAU", ask: 4300, bid: 4290 }]
  };
  globalThis.document = {
    getElementById: element,
    querySelectorAll: selector => selector === "[data-h]" ? buttons : [],
    addEventListener() {}
  };
  globalThis.fetch = async url => ({
    ok: true, json: async () => url.includes("history") ? history : spot
  });
  try {
    await import("../app_verified.mjs?horizon-fail-closed-regression");
    await new Promise(resolve => setTimeout(resolve, 0));
    assert.match(element("forecast").textContent, /\$/);
    assert.match(element("mae").textContent, /\$/);
    assert.notEqual(element("chart").innerHTML, "");

    buttons[2].handlers.click();
    for (const id of ["forecast", "target", "change", "range", "model", "mae", "base-mae", "coverage"])
      assert.equal(element(id).textContent, "—", id + " must be cleared");
    assert.equal(element("chart").innerHTML, "");
    assert.match(element("message").textContent, /تعذر التنبؤ/);

    buttons[1].handlers.click();
    assert.match(element("forecast").textContent, /\$/);
    assert.notEqual(element("chart").innerHTML, "");
  } finally {
    globalThis.document = oldDocument;
    globalThis.fetch = oldFetch;
  }
});
