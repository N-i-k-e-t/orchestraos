import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { OpsLayout } from "./components/ops/OpsLayout";
import { DemoPage } from "./pages/DemoPage";
import { IncidentsPage } from "./pages/IncidentsPage";
import { HealthPage } from "./pages/Health";
import { MetricsPage } from "./pages/MetricsPage";
import { OpsCenterPage } from "./pages/OpsCenter";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DemoPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="metrics" element={<MetricsPage />} />
          <Route path="health" element={<HealthPage />} />
        </Route>
        <Route element={<OpsLayout />}>
          <Route path="ops" element={<OpsCenterPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
