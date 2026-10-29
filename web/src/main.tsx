import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { initToken } from "./api";
import "./styles.css";

initToken();
// Opening a fresh launch link in a tab that already runs the app: adopt the new token.
window.addEventListener("hashchange", () => {
  if (/[#&]t=/.test(window.location.hash) && initToken()) window.location.reload();
});
const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
