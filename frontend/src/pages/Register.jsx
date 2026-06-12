// frontend/src/pages/Register.jsx

import { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import {
  TrendingDown,
  Mail,
  Lock,
  User,
  Loader,
} from "lucide-react"

export default function Register() {
  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
    confirm_password: "",
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const { register } = useAuth()
  const navigate = useNavigate()

  const handleChange = (e) => {
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    // Validate passwords
    if (form.password !== form.confirm_password) {
      setError("Passwords do not match")
      return
    }

    if (form.password.length < 6) {
      setError("Password must be at least 6 characters")
      return
    }

    setLoading(true)

    try {
      await register({
        email: form.email,
        username: form.username,
        password: form.password,
      })

      setSuccess(true)

      // Redirect after success
      setTimeout(() => {
        navigate("/login")
      }, 2000)
    } catch (err) {
      setError(err.message || "Registration failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800
                 flex items-center justify-center p-4"
    >
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-3">
            <div className="p-3 bg-blue-600 rounded-xl">
              <TrendingDown size={28} className="text-white" />
            </div>

            <h1 className="text-3xl font-bold text-white">
              ChurnAI
            </h1>
          </div>

          <p className="text-slate-400 text-sm">
            Create your account to get started
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl p-8 shadow-2xl">

          <h2 className="text-xl font-bold text-gray-800 mb-1">
            Create account
          </h2>

          <p className="text-gray-500 text-sm mb-6">
            Fill in your details to register
          </p>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">

            {/* Success Message */}
            {success && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-green-600 text-sm">
                  ✅ Account created! Redirecting to login...
                </p>
              </div>
            )}

            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>

              <div className="relative">
                <User
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                />

                <input
                  name="username"
                  type="text"
                  value={form.username}
                  onChange={handleChange}
                  required
                  placeholder="john_doe"
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-200
                             rounded-lg text-sm focus:outline-none
                             focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

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
                  type="password"
                  value={form.password}
                  onChange={handleChange}
                  required
                  placeholder="Min 6 characters"
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-200
                             rounded-lg text-sm focus:outline-none
                             focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Confirm Password
              </label>

              <div className="relative">
                <Lock
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                />

                <input
                  name="confirm_password"
                  type="password"
                  value={form.confirm_password}
                  onChange={handleChange}
                  required
                  placeholder="Repeat password"
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-200
                             rounded-lg text-sm focus:outline-none
                             focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-red-600 text-sm">
                  {error}
                </p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || success}
              className="w-full bg-blue-600 text-white py-2.5 rounded-lg
                         hover:bg-blue-700 transition font-medium text-sm
                         flex items-center justify-center gap-2
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader size={16} className="animate-spin" />
                  Creating account...
                </>
              ) : (
                "Create Account"
              )}
            </button>

          </form>

          {/* Login Link */}
          <p className="text-center text-sm text-gray-500 mt-4">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-blue-600 hover:underline font-medium"
            >
              Sign in
            </Link>
          </p>

        </div>
      </div>
    </div>
  )
}