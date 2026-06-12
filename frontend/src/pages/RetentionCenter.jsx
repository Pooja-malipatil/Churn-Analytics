import { useState, useEffect } from "react"
import {
  Heart, AlertTriangle, Phone,
  Mail, Tag, Shield, CheckCircle,
  Clock, Zap, Loader, RefreshCw
} from "lucide-react"
import API from "../services/api"

const RISK_STYLES = {
  Critical: {
    badge:  "bg-red-100 text-red-700 border border-red-200",
    border: "border-l-red-500",
  },
  High: {
    badge:  "bg-orange-100 text-orange-700 border border-orange-200",
    border: "border-l-orange-500",
  },
  Medium: {
    badge:  "bg-yellow-100 text-yellow-700 border border-yellow-200",
    border: "border-l-yellow-500",
  },
}

// Generate retention strategies based on customer data
function getStrategies(customer) {
  const strategies = []

  if (customer.contract === "Month-to-month") {
    strategies.push("Offer 20% discount to upgrade to annual contract")
  }
  if (customer.monthlyCharges > 70) {
    strategies.push("Offer 15% loyalty discount on monthly bill")
  }
  if (customer.tenure < 6) {
    strategies.push("Schedule onboarding call — new customer at risk")
  }
  if (customer.riskCategory === "Critical") {
    strategies.push("Assign dedicated account manager immediately")
    strategies.push("Schedule customer success call within 24 hours")
  }
  if (!strategies.length) {
    strategies.push("Send personalized re-engagement email campaign")
  }

  return strategies
}

function CustomerCard({ customer }) {
  const [expanded, setExpanded] = useState(false)
  const [actioned, setActioned] = useState(false)
  const style      = RISK_STYLES[customer.riskCategory] || RISK_STYLES["Medium"]
  const strategies = getStrategies(customer)

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-100
                     border-l-4 ${style.border}`}>

      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gray-100
                            flex items-center justify-center
                            font-medium text-gray-600 text-sm">
              {customer.id?.slice(0, 2)?.toUpperCase() || "??"}
            </div>
            <div>
              <p className="font-medium text-gray-800 text-sm">
                {customer.id}
              </p>
              <p className="text-xs text-gray-400">
                {customer.contract} · {customer.internetService}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2 py-1 rounded-full font-medium ${style.badge}`}>
              {customer.riskCategory}
            </span>
            <span className="text-lg font-bold text-gray-800">
              {(customer.churnProbability * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-3 bg-gray-100 rounded-full h-2">
          <div
            className="h-2 rounded-full"
            style={{
              width: `${customer.churnProbability * 100}%`,
              backgroundColor:
                customer.riskCategory === "Critical" ? "#ef4444" :
                customer.riskCategory === "High"     ? "#f97316" : "#f59e0b"
            }}
          />
        </div>

        {/* Stats */}
        <div className="mt-3 grid grid-cols-3 gap-2">
          <div className="text-center p-2 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-400">Tenure</p>
            <p className="text-sm font-medium text-gray-700">
              {customer.tenure} mo
            </p>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-400">Monthly</p>
            <p className="text-sm font-medium text-gray-700">
              ${customer.monthlyCharges}
            </p>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-400">Contract</p>
            <p className="text-xs font-medium text-gray-700">
              {customer.contract === "Month-to-month" ? "Monthly" : customer.contract}
            </p>
          </div>
        </div>
      </div>

      {/* Strategies */}
      <div className="border-t border-gray-100 px-4 py-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-between w-full text-sm
                     text-gray-600 hover:text-gray-800 transition"
        >
          <span className="flex items-center gap-1">
            <Zap size={14} className="text-yellow-500" />
            {strategies.length} Retention Strategies
          </span>
          <span>{expanded ? "▲" : "▼"}</span>
        </button>

        {expanded && (
          <div className="mt-3 space-y-2">
            {strategies.map((strategy, i) => (
              <div key={i}
                className="flex items-start gap-2 p-2 bg-gray-50 rounded-lg">
                <CheckCircle size={14} className="text-green-500 mt-0.5 shrink-0" />
                <p className="text-xs text-gray-600">{strategy}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="border-t border-gray-100 px-4 py-3">
        {actioned ? (
          <div className="flex items-center justify-center gap-2
                          py-2 bg-green-50 rounded-lg">
            <CheckCircle size={16} className="text-green-500" />
            <span className="text-sm text-green-600 font-medium">
              Action taken!
            </span>
          </div>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => setActioned(true)}
              className="flex-1 flex items-center justify-center gap-1
                         bg-blue-600 text-white py-2 rounded-lg
                         hover:bg-blue-700 transition text-xs font-medium"
            >
              <Phone size={12} /> Call
            </button>
            <button
              onClick={() => setActioned(true)}
              className="flex-1 flex items-center justify-center gap-1
                         bg-purple-600 text-white py-2 rounded-lg
                         hover:bg-purple-700 transition text-xs font-medium"
            >
              <Mail size={12} /> Email
            </button>
            <button
              onClick={() => setActioned(true)}
              className="flex-1 flex items-center justify-center gap-1
                         bg-green-600 text-white py-2 rounded-lg
                         hover:bg-green-700 transition text-xs font-medium"
            >
              <Tag size={12} /> Offer
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function RetentionCenter() {
  const [customers, setCustomers] = useState([])
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState(null)
  const [filter,    setFilter]    = useState("All")

  useEffect(() => {
    fetchAtRiskCustomers()
  }, [])

  const fetchAtRiskCustomers = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await API.get("/analytics/at-risk-customers")
      setCustomers(res.data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const filters  = ["All", "Critical", "High", "Medium"]
  const filtered = filter === "All"
    ? customers
    : customers.filter(c => c.riskCategory === filter)

  const critical = customers.filter(c => c.riskCategory === "Critical").length
  const high     = customers.filter(c => c.riskCategory === "High").length
  const medium   = customers.filter(c => c.riskCategory === "Medium").length
  const revenue  = customers.reduce((sum, c) => sum + c.monthlyCharges, 0).toFixed(0)

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Retention Center</h2>
          <p className="text-gray-500 text-sm mt-1">
            At-risk customers from your active dataset — ranked by churn probability
          </p>
        </div>
        <button
          onClick={fetchAtRiskCustomers}
          className="flex items-center gap-2 border border-gray-200
                     text-gray-600 px-3 py-2 rounded-lg
                     hover:bg-gray-50 transition text-sm"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-red-50 rounded-xl p-4 border border-red-100">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 bg-red-500 rounded-full" />
            <p className="text-xs text-red-600 font-medium">Critical Risk</p>
          </div>
          <p className="text-3xl font-bold text-red-700">{critical}</p>
          <p className="text-xs text-red-400">act immediately</p>
        </div>
        <div className="bg-orange-50 rounded-xl p-4 border border-orange-100">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 bg-orange-500 rounded-full" />
            <p className="text-xs text-orange-600 font-medium">High Risk</p>
          </div>
          <p className="text-3xl font-bold text-orange-700">{high}</p>
          <p className="text-xs text-orange-400">act this week</p>
        </div>
        <div className="bg-yellow-50 rounded-xl p-4 border border-yellow-100">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 bg-yellow-500 rounded-full" />
            <p className="text-xs text-yellow-600 font-medium">Medium Risk</p>
          </div>
          <p className="text-3xl font-bold text-yellow-700">{medium}</p>
          <p className="text-xs text-yellow-400">monitor closely</p>
        </div>
        <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
          <p className="text-xs text-blue-600 font-medium mb-1">Revenue at Risk</p>
          <p className="text-3xl font-bold text-blue-700">${Number(revenue).toLocaleString()}</p>
          <p className="text-xs text-blue-400">monthly if all churn</p>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {filters.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition
                ${filter === f
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
                }`}
            >
              {f}
              <span className="ml-1 text-xs opacity-70">
                ({f === "All"
                  ? customers.length
                  : customers.filter(c => c.riskCategory === f).length
                })
              </span>
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Clock size={12} />
          Sorted by churn probability
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center h-48">
          <div className="flex items-center gap-3 text-gray-500">
            <Loader size={20} className="animate-spin" />
            <span>Loading at-risk customers from dataset...</span>
          </div>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="bg-red-50 rounded-xl p-4 border border-red-200">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {/* Customer Cards */}
      {!loading && !error && (
        <>
          {filtered.length === 0 ? (
            <div className="bg-white rounded-xl p-8 text-center
                            shadow-sm border border-gray-100">
              <Heart size={32} className="text-gray-200 mx-auto mb-3" />
              <p className="text-gray-400 text-sm">
                No {filter !== "All" ? filter.toLowerCase() + " risk" : ""} customers found
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((customer, i) => (
                <CustomerCard key={i} customer={customer} />
              ))}
            </div>
          )}
        </>
      )}

    </div>
  )
}