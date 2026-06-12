// frontend/src/context/AuthContext.jsx

import { createContext, useContext, useState, useEffect } from "react"
import { loginUser, registerUser } from "../services/api"

// WHY Context:
// Without context, you'd pass user data as props
// through every component — called "prop drilling"
// Context makes data available to ANY component
// without passing it down manually
// This is how auth works in every real React app

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null)
  const [loading, setLoading] = useState(true)

  // Check if user is already logged in on app start
  useEffect(() => {
    const storedUser  = localStorage.getItem("user")
    const storedToken = localStorage.getItem("token")

    if (storedUser && storedToken) {
      setUser(JSON.parse(storedUser))
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    const response = await loginUser({ email, password })

    // Store token and user in localStorage
    // WHY localStorage: persists across page refreshes
    // In production: use httpOnly cookies for security
    localStorage.setItem("token", response.access_token)
    localStorage.setItem("user",  JSON.stringify(response.user))

    setUser(response.user)
    return response
  }

  const register = async (data) => {
    const response = await registerUser(data)
    return response
  }

  const logout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    setUser(null)
  }

  const isAuthenticated = !!user
  // !! converts any value to boolean
  // null → false, {id:1} → true

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      logout,
      isAuthenticated,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

// Custom hook — cleaner way to use auth context
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider")
  }
  return context
}