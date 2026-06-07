import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { DemoPage } from "./pages/DemoPage";
import { IncidentsPage } from "./pages/IncidentsPage";
import { MetricsPage } from "./pages/MetricsPage";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DemoPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="metrics" element={<MetricsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
