// frontend/src/components/ProtectedRoute.jsx

import { Navigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

// WHY ProtectedRoute:
// Some pages should only be accessible when logged in
// ProtectedRoute checks if user is authenticated
// If not → redirects to login page automatically
// This is the standard pattern used in every React app

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  // Still checking localStorage — show nothing
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  // Not logged in → redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Logged in → show the page
  return children
}