// frontend/src/pages/Login.jsx

import { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { TrendingDown, Mail, Lock, Loader, Eye, EyeOff } from "lucide-react"

export default function Login() {
  const [form,        setForm]        = useState({ email: "", password: "" })
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState(null)
  const [showPassword,setShowPassword]= useState(false)

  const { login }    = useAuth()
  const navigate     = useNavigate()

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      await login(form.email, form.password)
      navigate("/dashboard")
      // After login → redirect to dashboard
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Quick fill for demo
  const fillDemo = () => {
    setForm({
      email:    "john@example.com",
      password: "securepassword123",
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800
                    flex items-center justify-center p-4">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-3">
            <div className="p-3 bg-blue-600 rounded-xl">
              <TrendingDown size={28} className="text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">ChurnAI</h1>
          </div>
          <p className="text-slate-400 text-sm">
            AI-Powered Customer Retention Platform
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl p-8 shadow-2xl">

          <h2 className="text-xl font-bold text-gray-800 mb-1">
            Welcome back
          </h2>
          <p className="text-gray-500 text-sm mb-6">
            Sign in to your account to continue
          </p>

          {/* Demo button */}
          <button
            type="button"
            onClick={fillDemo}
            className="w-full mb-4 py-2 border border-dashed border-blue-300
                      text-blue-600 rounded-lg text-sm hover:bg-blue-50 transition"
          >
            Fill Demo Credentials
          </button>

          <form onSubmit={handleSubmit} className="space-y-4">

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <div className="relative">
                <Mail
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                />
                <input
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={handleChange}
                  required
                  placeholder="john@example.com"
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-200
                            rounded-lg text-sm focus:outline-none
                            focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <Lock
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                />
                <input
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={form.password}
                  onChange={handleChange}
                  required
                  placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-2.5 border border-gray-200
                            rounded-lg text-sm focus:outline-none
                            focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2.5 rounded-lg
                         hover:bg-blue-700 transition font-medium text-sm
                         flex items-center justify-center gap-2
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading
                ? <><Loader size={16} className="animate-spin" /> Signing in...</>
                : "Sign In"
              }
            </button>

          </form>

          {/* Register link */}
          <p className="text-center text-sm text-gray-500 mt-4">
            Don't have an account?{" "}
            <Link
              to="/register"
              className="text-blue-600 hover:underline font-medium"
            >
              Create one
            </Link>
          </p>

        </div>

        {/* Footer */}
        <p className="text-center text-slate-500 text-xs mt-6">
          AI-Powered Churn Prediction Platform v1.0
        </p>

      </div>
    </div>
  )
}