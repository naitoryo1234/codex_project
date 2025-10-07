import React, { useEffect, useMemo, useRef, useState } from "react";
import ReactDOM from "react-dom/client";
import { Streamlit } from "streamlit-component-lib";

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

const ITEMS: KoyakuItem[] = [
  { key: "bell", label: "ベル", color: "#f7d94c", textColor: "#1f1f1f" },
  { key: "cherry", label: "チェリー", color: "#ef5a5a", textColor: "#ffffff" },
  { key: "watermelon", label: "スイカ", color: "#4caf50", textColor: "#ffffff" },
  { key: "replay", label: "リプレイ", color: "#4ac0ff", textColor: "#0e2d3c" },
  { key: "chance", label: "チャンス目", color: "#b085f5", textColor: "#1f1f1f" }
];

const STORAGE_KEY_COUNTS = "koyakuCounter_counts";
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

const buildTapButtonStyle = (
  themeStyle: ThemeStyle,
  variant: "increment" | "decrement"
): React.CSSProperties => {
  const size = variant === "increment" ? 3.3 : 2.6;
  const fontSize = variant === "increment" ? "1.9rem" : "1.5rem";

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

const KoyakuCounter: React.FC = () => {
  const [counts, setCounts] = useState<number[]>(getInitialCounts);
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [undoCounts, setUndoCounts] = useState<number[] | null>(null);
  const undoTimerRef = useRef<number | null>(null);

  const persistCounts = (nextCounts: number[]) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY_COUNTS, JSON.stringify(nextCounts));
    }
  };

  useEffect(() => {
    persistCounts(counts);
    Streamlit.setFrameHeight();
  }, [counts]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY_THEME, theme);
    }
    Streamlit.setFrameHeight();
  }, [theme]);

  useEffect(() => {
    Streamlit.setFrameHeight();
    return () => {
      if (undoTimerRef.current) {
        window.clearTimeout(undoTimerRef.current);
      }
    };
  }, []);

  const clearUndo = () => {
    if (undoTimerRef.current) {
      window.clearTimeout(undoTimerRef.current);
      undoTimerRef.current = null;
    }
    setUndoCounts(null);
  };

  const themeStyle = themeConfig[theme];

  const total = useMemo(
    () => counts.reduce((acc, value) => acc + value, 0),
    [counts]
  );

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

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  const handleReset = () => {
    setUndoCounts(counts);
    setCounts(ITEMS.map(() => 0));
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
    setCounts(undoCounts);
    clearUndo();
  };

  return (
    <div
      style={{
        fontFamily: "'Noto Sans JP', 'Hiragino Sans', 'Yu Gothic', sans-serif",
        padding: "1rem",
        background: themeStyle.rootBg,
        color: themeStyle.text,
        minWidth: "280px",
        maxWidth: "560px",
        margin: "0 auto",
        transition: "background 0.2s ease, color 0.2s ease"
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "1rem",
          marginBottom: "1rem"
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: "1.5rem" }}>小役カウンター</h2>
          <p
            style={{
              margin: "0.25rem 0 0",
              fontWeight: 600,
              color: themeStyle.secondaryText
            }}
          >
            合計: {total}
          </p>
        </div>
        <button
          onClick={toggleTheme}
          style={{
            border: "none",
            borderRadius: "999px",
            padding: "0.6rem 1rem",
            background: themeStyle.buttonBg,
            color: themeStyle.buttonText,
            fontSize: "0.95rem",
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "0.4rem",
            touchAction: "manipulation"
          }}
          aria-label="テーマ切り替え"
        >
          {theme === "light" ? "🌙 ダーク" : "🌞 ライト"}
        </button>
      </div>

      <div style={{ display: "grid", gap: "0.85rem" }}>
        {ITEMS.map((item, index) => {
          const labelForA11y = `${item.label ?? "小役"}${index + 1}`;
          return (
            <div
              key={item.key}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.65rem",
                padding: "0.85rem 0.9rem",
                borderRadius: "0.9rem",
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
                aria-label={`${labelForA11y} を 1 減算`}
              >
                -
              </button>
              <input
                type="number"
                min={0}
                inputMode="numeric"
                pattern="[0-9]*"
                value={counts[index]}
                onChange={(event) => handleDirectInput(index, event.target.value)}
                style={{
                  width: "3.2rem",
                  height: "2.5rem",
                  borderRadius: "0.65rem",
                  border: "none",
                  textAlign: "center",
                  fontSize: "1.25rem",
                  fontWeight: 700,
                  color: item.textColor,
                  background: "rgba(255, 255, 255, 0.55)",
                  outline: "none"
                }}
                aria-label={`${labelForA11y} のカウントを直接入力`}
              />
              <button
                onClick={() => handleUpdate(index, 1)}
                style={buildTapButtonStyle(themeStyle, "increment")}
                aria-label={`${labelForA11y} を 1 加算`}
              >
                +
              </button>
            </div>
          );
        })}
      </div>

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
            aria-label="リセットを取り消す"
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
            fontSize: "1rem",
            fontWeight: 600,
            cursor: "pointer",
            touchAction: "manipulation"
          }}
          aria-label="すべての小役カウントをリセット"
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

const render = () => {
  root.render(<KoyakuCounter />);
};

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, () => {
  Streamlit.setComponentReady();
  render();
  Streamlit.setFrameHeight();
});

Streamlit.setComponentReady();
render();
Streamlit.setFrameHeight();