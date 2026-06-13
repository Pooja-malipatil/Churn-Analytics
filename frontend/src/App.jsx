import { Routes, Route, Navigate } from "react-router-dom"
import { AuthProvider } from "./context/AuthContext"
import { DataProvider } from "./context/DataContext"
import ProtectedRoute from "./components/ProtectedRoute"
import Layout from "./components/layout/Layout"
import Dashboard from "./pages/Dashboard"
import PredictCustomer from "./pages/PredictCustomer"
import Analytics from "./pages/Analytics"
import RetentionCenter from "./pages/RetentionCenter"
import UploadDataset from "./pages/UploadDataset"
import Login from "./pages/Login"
import Register from "./pages/Register"
import Customers from "./pages/Customer"

export default function App() {
  return (
    <AuthProvider>
      <DataProvider>
        <Routes>
          <Route path="/login"    element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="predict"   element={<PredictCustomer />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="retention" element={<RetentionCenter />} />
            <Route path="upload"    element={<UploadDataset />} />
            <Route path="customers" element={<Customers />} />
          </Route>
        </Routes>
      </DataProvider>
    </AuthProvider>
  )
}