import { Streamlit } from "streamlit-component-lib";
import "./style.css";

console.log("SwipeCounter build:", __BUILD_ID__, navigator.userAgent);

const appRoot = document.getElementById("app");

if (!appRoot) {
  throw new Error("Swipe counter root not found");
}

appRoot.innerHTML = `
  <div class="counter-root">
    <div class="counter-header">
      <span class="counter-label" id="counter-label">小役回数</span>
      <span class="counter-value" id="counter-value">0</span>
    </div>
    <div class="counter-gesture" id="counter-gesture">
      上にスワイプで +1 ／ 下にスワイプで -1
    </div>
    <div class="counter-controls">
      <button type="button" data-delta="-1">-1</button>
      <input type="number" id="counter-input" min="0" step="1" inputmode="numeric" />
      <button type="button" data-delta="1">+1</button>
      <button type="button" data-action="reset" class="reset-btn">リセット</button>
    </div>
    <p class="counter-caption" id="counter-caption"></p>
  </div>
`;

const valueEl = document.getElementById("counter-value");
const gestureEl = document.getElementById("counter-gesture");
const inputEl = document.getElementById("counter-input");
const labelEl = document.getElementById("counter-label");
const captionEl = document.getElementById("counter-caption");
const buttons = Array.from(document.querySelectorAll("[data-delta]"));
const resetBtn = document.querySelector("[data-action=reset]");

const MIN_VALUE = 0;
let storageKey = "swipe_counter_storage";
let value = 0;
let pointerStartY = null;
let hasHydrated = false;
let updatingFromPython = false;

const frameResize = () => Streamlit.setFrameHeight(document.body.scrollHeight);

const clamp = (num) => {
  if (!Number.isFinite(num)) {
    return MIN_VALUE;
  }
  return Math.max(MIN_VALUE, Math.round(num));
};

const render = (newValue) => {
  const displayValue = clamp(newValue);
  valueEl.textContent = displayValue.toString();
  inputEl.value = displayValue;
  frameResize();
};

const persist = (newValue) => {
  const payload = { value: newValue, updatedAt: Date.now() };
  try {
    window.localStorage.setItem(storageKey, JSON.stringify(payload));
  } catch (error) {
    console.warn("swipe-counter: localStorage write failed", error);
  }
};

const syncToStreamlit = (origin) => {
  if (updatingFromPython) {
    return;
  }
  Streamlit.setComponentValue({ value, origin });
};

const apply = (newValue, options = {}) => {
  const opts = {
    notify: true,
    persist: true,
    origin: "user",
    ...options,
  };
  value = clamp(newValue);
  render(value);
  if (opts.persist) {
    persist(value);
  }
  if (opts.notify) {
    syncToStreamlit(opts.origin);
  }
};

const adjust = (delta) => {
  if (!delta) {
    return;
  }
  apply(value + delta, { origin: "adjust" });
};

const hydrateFromStorage = () => {
  if (hasHydrated) {
    return false;
  }
  hasHydrated = true;
  try {
    const stored = window.localStorage.getItem(storageKey);
    if (!stored) {
      return false;
    }
    const parsed = JSON.parse(stored);
    if (parsed && typeof parsed.value === "number") {
      value = clamp(parsed.value);
      render(value);
      syncToStreamlit("storage");
      return true;
    }
  } catch (error) {
    console.warn("swipe-counter: localStorage read failed", error);
  }
  return false;
};

const onRender = (event) => {
  const detail = event.detail || {};
  const args = detail.args || {};
  const incomingValue = clamp(Number(args.value ?? value));

  storageKey = typeof args.storage_key === "string" && args.storage_key.trim()
    ? args.storage_key.trim()
    : storageKey;

  labelEl.textContent = args.label || "小役回数";
  captionEl.textContent =
    args.description || "上スワイプで+1 / 下スワイプで-1。非対応の環境では入力欄をご利用ください。";

  const hydrated = hydrateFromStorage();

  if (!hydrated) {
    if (incomingValue !== value) {
      updatingFromPython = true;
      apply(incomingValue, { notify: false, origin: "python" });
      updatingFromPython = false;
    } else {
      render(value);
    }
    syncToStreamlit("init");
  } else if (incomingValue !== value) {
    updatingFromPython = true;
    apply(incomingValue, { notify: false, origin: "python" });
    updatingFromPython = false;
  }

  frameResize();
};

gestureEl.addEventListener("pointerdown", (event) => {
  pointerStartY = event.clientY;
  gestureEl.setPointerCapture(event.pointerId);
  gestureEl.classList.add("active");
});

gestureEl.addEventListener("pointerup", (event) => {
  if (pointerStartY === null) {
    return;
  }
  const deltaY = event.clientY - pointerStartY;
  const threshold = 28;
  if (deltaY <= -threshold) {
    adjust(1);
  } else if (deltaY >= threshold) {
    adjust(-1);
  }
  pointerStartY = null;
  gestureEl.classList.remove("active");
  try {
    gestureEl.releasePointerCapture(event.pointerId);
  } catch (error) {
    // ignore release errors
  }
});

gestureEl.addEventListener("pointercancel", () => {
  pointerStartY = null;
  gestureEl.classList.remove("active");
});

gestureEl.addEventListener(
  "touchmove",
  (event) => {
    if (pointerStartY === null) {
      return;
    }
    event.preventDefault();
  },
  { passive: false }
);

buttons.forEach((btn) => {
  btn.addEventListener("click", () => {
    const delta = Number(btn.dataset.delta);
    adjust(delta);
  });
});

if (resetBtn) {
  resetBtn.addEventListener("click", () => {
    apply(MIN_VALUE, { origin: "reset" });
  });
}

inputEl.addEventListener("change", () => {
  const parsed = clamp(Number(inputEl.value));
  apply(parsed, { origin: "input" });
});

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
Streamlit.setComponentReady();
frameResize();