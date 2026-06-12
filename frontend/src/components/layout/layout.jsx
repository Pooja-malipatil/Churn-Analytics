import { Outlet, NavLink } from "react-router-dom"
import {
  LayoutDashboard, Brain,
  BarChart3, Heart,
  TrendingDown, Menu, X,Upload
} from "lucide-react"
import { useState } from "react"
import { useAuth } from "../../context/AuthContext"

const NAV_ITEMS = [
  { path: "/dashboard", label: "Dashboard",        icon: LayoutDashboard },
  { path: "/predict",   label: "Predict Churn",    icon: Brain           },
  { path: "/analytics", label: "Analytics",        icon: BarChart3       },
  { path: "/retention", label: "Retention Center", icon: Heart           },
  { path: "/upload",    label: "Upload Dataset",   icon: Upload          },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { user, logout } = useAuth()

  return (
    <div className="flex h-screen bg-gray-50">

      {/* SIDEBAR */}
      <aside className={`
        ${sidebarOpen ? "w-64" : "w-16"}
        bg-slate-900 text-white
        transition-all duration-300
        flex flex-col shrink-0
      `}>

        {/* Logo */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <TrendingDown className="text-blue-400" size={24} />
              <span className="font-bold text-sm">ChurnAI</span>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 rounded hover:bg-slate-700 transition"
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 p-2 space-y-1 mt-2">
          {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) => `
                flex items-center gap-3 px-3 py-2.5 rounded-lg
                transition-all duration-200 text-sm
                ${isActive
                  ? "bg-blue-600 text-white font-medium"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
                }
              `}
            >
              <Icon size={18} className="shrink-0" />
              {sidebarOpen && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer with user info */}
        {sidebarOpen && (
          <div className="p-4 border-t border-slate-700">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 bg-blue-600 rounded-full
                              flex items-center justify-center
                              text-xs font-bold text-white">
                {user?.username?.[0]?.toUpperCase() || "U"}
              </div>
              <div>
                <p className="text-xs text-slate-300">
                  {user?.full_name || user?.username}
                </p>
                <p className="text-xs text-slate-500">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="w-full text-xs text-slate-400
                         hover:text-red-400 transition text-left py-1"
            >
              → Sign out
            </button>
          </div>
        )}

        {/* Collapsed footer */}
        {!sidebarOpen && (
          <div className="p-2 border-t border-slate-700">
            <button
              onClick={logout}
              className="w-full p-2 text-slate-400
                         hover:text-red-400 transition text-center text-xs"
            >
              →
            </button>
          </div>
        )}

      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 overflow-auto">

        {/* Top bar */}
        <header className="bg-white border-b border-gray-200
                           px-6 py-4 sticky top-0 z-10">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-semibold text-gray-800">
              Customer Churn Prediction Platform
            </h1>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs text-gray-500">API Connected</span>
            </div>
          </div>
        </header>

        {/* Page renders here */}
        <div className="p-6">
          <Outlet />
        </div>

      </main>
    </div>
  )
}