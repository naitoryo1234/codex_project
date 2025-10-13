import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactDOM from "react-dom/client";
import { Streamlit } from "streamlit-component-lib";

declare const __BUILD_ID__: string;

console.log("KoyakuCounter build:", __BUILD_ID__, navigator.userAgent);

type Theme = "light" | "dark";

type ThemeStyle = {
  rootBg: string;
  text: string;
  secondaryText: string;
  cardShadow: string;
  buttonBg: string;
  buttonText: string;
  resetBg: string;
  resetText: string;
  cardBorder: string;
};

type KoyakuItem = {
  key: string;
  label: string;
  color: string;
  textColor: string;
};
type KoyakuCounterProps = {
  isReady: boolean;
};


const ITEMS: KoyakuItem[] = [
  { key: "bell", label: "ベル", color: "#f7d94c", textColor: "#1f1f1f" },
  { key: "weak_cherry", label: "弱チェリー", color: "#ef5a5a", textColor: "#ffffff" },
  { key: "strong_cherry", label: "強チェリー", color: "#d45d79", textColor: "#ffffff" },
  { key: "watermelon", label: "スイカ", color: "#4caf50", textColor: "#ffffff" },
  { key: "chance", label: "チャンス目", color: "#b085f5", textColor: "#1f1f1f" },
  { key: "replay", label: "リプレイ", color: "#4ac0ff", textColor: "#0e2d3c" },
  { key: "boat", label: "ボート", color: "#ffca28", textColor: "#1f1f1f" },
  { key: "mb", label: "MB", color: "#8d6e63", textColor: "#ffffff" },
  { key: "common_bell", label: "共通ベル", color: "#ffab91", textColor: "#1f1f1f" },
  { key: "others", label: "その他", color: "#90a4ae", textColor: "#1f1f1f" }
];

const MAIN_ITEM_COUNT = 6;
const MAIN_ITEMS = ITEMS.slice(0, MAIN_ITEM_COUNT);
const EXTRA_ITEMS = ITEMS.slice(MAIN_ITEM_COUNT);

const STORAGE_KEY_COUNTS = "koyakuCounter_counts";
const STORAGE_KEY_SHOW_EXTRAS = "koyakuCounter_showExtras";

const STORAGE_KEY_THEME = "koyakuCounter_theme";
const UNDO_TIMEOUT = 10000; // 10 秒以内なら復元可能

const themeConfig: Record<Theme, ThemeStyle> = {
  light: {
    rootBg: "#fdfdf6",
    text: "#1f1f1f",
    secondaryText: "#4f4f4f",
    cardShadow: "0 2px 6px rgba(0, 0, 0, 0.12)",
    buttonBg: "rgba(255, 255, 255, 0.92)",
    buttonText: "#1f1f1f",
    resetBg: "#424242",
    resetText: "#ffffff",
    cardBorder: "1px solid rgba(0, 0, 0, 0.05)"
  },
  dark: {
    rootBg: "#121212",
    text: "#f4f4f4",
    secondaryText: "#bdbdbd",
    cardShadow: "0 2px 8px rgba(0, 0, 0, 0.45)",
    buttonBg: "rgba(0, 0, 0, 0.35)",
    buttonText: "#f4f4f4",
    resetBg: "#616161",
    resetText: "#ffffff",
    cardBorder: "1px solid rgba(255, 255, 255, 0.12)"
  }
};

const getInitialCounts = (): number[] => {
  if (typeof window === "undefined") {
    return ITEMS.map(() => 0);
  }
  const raw = window.localStorage.getItem(STORAGE_KEY_COUNTS);
  if (!raw) {
    return ITEMS.map(() => 0);
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (Array.isArray(parsed)) {
      return ITEMS.map((_, index) => {
        const value = Number(parsed[index]);
        if (!Number.isFinite(value) || value < 0) {
          return 0;
        }
        return Math.floor(value);
      });
    }
  } catch (_error) {
    // 破損したデータは無視して初期値に戻す
  }
  return ITEMS.map(() => 0);
};

const getInitialTheme = (): Theme => {
  if (typeof window === "undefined") {
    return "light";
  }
  const saved = window.localStorage.getItem(STORAGE_KEY_THEME);
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
};

const getInitialShowExtras = (): boolean => {
  if (typeof window === "undefined") {
    return false;
  }
  const stored = window.localStorage.getItem(STORAGE_KEY_SHOW_EXTRAS);
  return stored === "1";
};


const buildTapButtonStyle = (
  themeStyle: ThemeStyle,
  variant: "increment" | "decrement"
): React.CSSProperties => {
  const size = variant === "increment" ? 2.8 : 2.2;
  const fontSize = variant === "increment" ? "1.55rem" : "1.15rem";

  return {
    width: `${size}rem`,
    height: `${size}rem`,
    borderRadius: "50%",
    border: "none",
    background: themeStyle.buttonBg,
    color: themeStyle.buttonText,
    fontSize,
    fontWeight: 700,
    cursor: "pointer",
    touchAction: "manipulation",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: themeStyle.cardShadow
  };
};

const KoyakuCounter: React.FC<KoyakuCounterProps> = ({ isReady }) => {
  const [counts, setCounts] = useState<number[]>(getInitialCounts);
  const theme = useMemo(() => getInitialTheme(), []);
  const [undoCounts, setUndoCounts] = useState<number[] | null>(null);
  const [showExtras, setShowExtras] = useState<boolean>(() => getInitialShowExtras());
  const undoTimerRef = useRef<number | null>(null);


  const pushCountsToStreamlit = useCallback((nextCounts: number[]) => {
    if (!isReady) {
      return;
    }
    Streamlit.setComponentValue({
      primaryCount: nextCounts[0] ?? 0,
      counts: [...nextCounts]
    });
  }, [isReady]);

  const persistCounts = (nextCounts: number[]) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY_COUNTS, JSON.stringify(nextCounts));
    }
  };

  useEffect(() => {
    persistCounts(counts);
    if (isReady) {
      Streamlit.setFrameHeight();
    }
  }, [counts, isReady]);

  useEffect(() => {
    if (!isReady) {
      return;
    }
    pushCountsToStreamlit(counts);
  }, [isReady, counts, pushCountsToStreamlit]);

  useEffect(() => {
    if (isReady) {
      Streamlit.setFrameHeight();
    }
    return () => {
      if (undoTimerRef.current) {
        window.clearTimeout(undoTimerRef.current);
      }
    };
  }, [isReady]);
  useEffect(() => {
    if (typeof window !== "undefined") {
            <span>{showExtras ? "追加カウンターを閉じる" : "追加カウンターを表示"}</span>
    }
  }, [showExtras]);



  const clearUndo = () => {
    if (undoTimerRef.current) {
      window.clearTimeout(undoTimerRef.current);
      undoTimerRef.current = null;
    }
    setUndoCounts(null);
  };

  const themeStyle = themeConfig[theme];
  const extraTotal = EXTRA_ITEMS.reduce((sum, _item, offset) => {
    const value = counts[MAIN_ITEM_COUNT + offset];
    return sum + (typeof value === "number" && Number.isFinite(value) ? value : 0);
  }, 0);

  const mainTotal = MAIN_ITEMS.reduce((sum, _item, index) => {
    const value = counts[index];
    return sum + (typeof value === "number" && Number.isFinite(value) ? value : 0);
  }, 0);

  const overallTotal = mainTotal + extraTotal;


  const renderCard = (item: KoyakuItem, index: number) => {
    const labelForA11y = `${item.label ?? "小役"}${index + 1}`;
    const currentValue = typeof counts[index] === "number" && Number.isFinite(counts[index]) ? counts[index] : 0;
    return (
      <div
        key={item.key}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "0.35rem",
          padding: "0.55rem 0.6rem",
          borderRadius: "0.75rem",
          background: item.color,
          color: item.textColor,
          boxShadow: themeStyle.cardShadow,
          border: themeStyle.cardBorder,
          transition: "transform 0.1s ease",
          touchAction: "manipulation"
        }}
      >
        <button
          onClick={() => handleUpdate(index, -1)}
          style={buildTapButtonStyle(themeStyle, "decrement")}
          aria-label={`${labelForA11y} を1減算`}
        >
          -
        </button>
        <input
          type="number"
          min={0}
          inputMode="numeric"
          pattern="[0-9]*"
          value={currentValue === 0 ? "" : String(currentValue)}
          onChange={(event) => handleDirectInput(index, event.target.value)}
          style={{
            width: "2.4rem",
            height: "1.9rem",
            borderRadius: "0.55rem",
            border: "none",
            textAlign: "center",
            fontSize: "1rem",
            fontWeight: 700,
            color: item.textColor,
            background: "rgba(255, 255, 255, 0.6)",
            outline: "none"
          }}
          aria-label={`${labelForA11y} のカウント入力`}
        />
        <button
          onClick={() => handleUpdate(index, 1)}
          style={buildTapButtonStyle(themeStyle, "increment")}
          aria-label={`${labelForA11y} を1加算`}
        >
          +
        </button>
      </div>
    );
  };




  const handleUpdate = (index: number, delta: number) => {
    setCounts((prev) =>
      prev.map((value, i) => {
        if (i !== index) {
          return value;
        }
        const next = value + delta;
        return next < 0 ? 0 : next;
      })
    );
    if (undoCounts) {
      clearUndo();
    }
  };

  const handleDirectInput = (index: number, rawValue: string) => {
    const numeric = Number(rawValue);
    const nextValue = Number.isFinite(numeric) && numeric >= 0 ? Math.floor(numeric) : 0;
    setCounts((prev) =>
      prev.map((value, i) => (i === index ? nextValue : value))
    );
    if (undoCounts) {
      clearUndo();
    }
  };

  const handleReset = () => {
    setUndoCounts([...counts]);
    const resetCounts = ITEMS.map(() => 0);
    setCounts(resetCounts);
    if (undoTimerRef.current) {
      window.clearTimeout(undoTimerRef.current);
    }
    undoTimerRef.current = window.setTimeout(() => {
      setUndoCounts(null);
      undoTimerRef.current = null;
    }, UNDO_TIMEOUT);
  };

  const handleUndo = () => {
    if (!undoCounts) {
      return;
    }
    const restored = [...undoCounts];
    setCounts(restored);
    clearUndo();
  };

  return (
    <div
      style={{
        fontFamily: "'Noto Sans JP', 'Hiragino Sans', 'Yu Gothic', sans-serif",
        padding: "1.2rem 1rem 1.35rem",
        background: themeStyle.rootBg,
        color: themeStyle.text,
        minWidth: "0",
        maxWidth: "420px",
        width: "100%",
        boxSizing: "border-box",
        margin: "0 auto",
        transition: "background 0.2s ease, color 0.2s ease"
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "0.45rem",
          color: themeStyle.secondaryText,
          fontSize: "0.82rem",
          fontWeight: 600,
          fontVariantNumeric: "tabular-nums"
        }}
      >
        <span>メイン {mainTotal}</span>
        <span>総計 {overallTotal}</span>
      </div>

      <div style={{ display: "grid", gap: "0.55rem", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))" }}>
        {MAIN_ITEMS.map((item, index) => renderCard(item, index))}
      </div>

      {EXTRA_ITEMS.length > 0 && (
        <div style={{ marginTop: "0.9rem" }}>
          <button
            onClick={() => setShowExtras((prev) => !prev)}
            style={{
              width: "100%",
              border: "1px solid rgba(0, 0, 0, 0.08)",
              borderRadius: "0.75rem",
              padding: "0.55rem 0.8rem",
              background: theme === "light" ? "rgba(255, 255, 255, 0.92)" : "rgba(0, 0, 0, 0.35)",
              color: themeStyle.text,
              fontSize: "0.95rem",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "0.65rem",
              cursor: "pointer",
              touchAction: "manipulation"
            }}
            aria-expanded={showExtras}
            aria-controls="extra-counter-grid"
          >
            <span>{showExtras ? "追加カウンターを閉じる" : "追加カウンターを表示"}</span>
            <span style={{ fontVariantNumeric: "tabular-nums" }}>追加計 {extraTotal}</span>
          </button>
          {showExtras && (
            <div
              id="extra-counter-grid"
              style={{
                marginTop: "0.6rem",
                display: "grid",
                gap: "0.7rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))"
              }}
            >
              {EXTRA_ITEMS.map((item, extraIndex) => renderCard(item, MAIN_ITEM_COUNT + extraIndex))}
            </div>
          )}
        </div>
      )}


      <div
        style={{
          marginTop: "1.25rem",
          display: "flex",
          justifyContent: undoCounts ? "space-between" : "flex-end",
          alignItems: "center",
          gap: "0.75rem"
        }}
      >
        {undoCounts && (
          <button
            onClick={handleUndo}
            style={{
              border: "none",
              borderRadius: "0.75rem",
              padding: "0.65rem 1rem",
              background: theme === "light" ? "#1976d2" : "#90caf9",
              color: theme === "light" ? "#ffffff" : "#0d1b2a",
              fontSize: "0.95rem",
              fontWeight: 600,
              cursor: "pointer",
              touchAction: "manipulation"
            }}
            aria-label="直前の変更を取り消す"
          >
            元に戻す
          </button>
        )}
        <button
          onClick={handleReset}
          style={{
            border: "none",
            borderRadius: "0.75rem",
            padding: "0.7rem 1.4rem",
            background: themeStyle.resetBg,
            color: themeStyle.resetText,
            fontSize: "1.1rem",
            fontWeight: 600,
            cursor: "pointer",
            touchAction: "manipulation"
          }}
          aria-label="すべてのカウントをリセット"
        >
          すべてリセット
        </button>
      </div>
    </div>
  );
};

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Failed to find the root element");
}

const root = ReactDOM.createRoot(rootElement);

let streamlitReady = false;
let initialRenderDone = false;

const render = () => {
  root.render(<KoyakuCounter isReady={streamlitReady} />);
};

const markReadyAndRender = () => {
  if (!streamlitReady) {
    streamlitReady = true;
    Streamlit.setComponentReady();
  }
  render();
  Streamlit.setFrameHeight();
};

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, () => {
  markReadyAndRender();
});

render();
Streamlit.setComponentReady();
Streamlit.setFrameHeight();








