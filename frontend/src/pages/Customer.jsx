import { useState, useEffect } from "react"
import {
  Search, Trash2, Eye, RefreshCw,
  TrendingDown, AlertTriangle,
  CheckCircle, Loader, ChevronLeft,
  ChevronRight, Users, Brain
} from "lucide-react"
import {
  getAllPredictions,
  getCustomerPredictions,
  getPredictionStats,
  deletePrediction,
} from "../services/api"

const RISK_STYLES = {
  Critical: "bg-red-100 text-red-700 border border-red-200",
  High:     "bg-orange-100 text-orange-700 border border-orange-200",
  Medium:   "bg-yellow-100 text-yellow-700 border border-yellow-200",
  Low:      "bg-green-100 text-green-700 border border-green-200",
}

function StatCard({ title, value, color, icon: Icon }) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} className={color} />
        <p className="text-xs text-gray-500">{title}</p>
      </div>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  )
}

export default function Customers() {
  const [predictions,  setPredictions]  = useState([])
  const [stats,        setStats]        = useState(null)
  const [loading,      setLoading]      = useState(true)
  const [search,       setSearch]       = useState("")
  const [riskFilter,   setRiskFilter]   = useState("All")
  const [page,         setPage]         = useState(1)
  const [totalPages,   setTotalPages]   = useState(1)
  const [total,        setTotal]        = useState(0)
  const [selected,     setSelected]     = useState(null)
  const [detailLoading,setDetailLoading]= useState(false)
  const [customerDetail,setCustomerDetail] = useState(null)
  const limit = 10

   useEffect(() => {
    fetchData()
    fetchStats()
  }, [])
  
  
  useEffect(() => {
    fetchData()
  }, [page, riskFilter])

 

  const fetchData = async () => {
    setLoading(true)
    try {
      const data = await getAllPredictions(
        page, limit,
        riskFilter !== "All" ? riskFilter : null,
        search || null
      )
      setPredictions(data.predictions || [])
      setTotalPages(data.total_pages  || 1)
      setTotal(data.total             || 0)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const data = await getPredictionStats()
      setStats(data)
    } catch (err) {
      console.error(err)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    fetchData()
  }

  const handleViewCustomer = async (customerId) => {
    setSelected(customerId)
    setDetailLoading(true)
    try {
      const data = await getCustomerPredictions(customerId)
      setCustomerDetail(data)
    } catch (err) {
      console.error(err)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this prediction?")) return
    try {
      await deletePrediction(id)
      fetchData()
      fetchStats()
      if (customerDetail) {
        setCustomerDetail(prev => ({
          ...prev,
          predictions: prev.predictions.filter(p => p.id !== id)
        }))
      }
    } catch (err) {
      console.error(err)
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A"
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short", day: "numeric",
      year: "numeric", hour: "2-digit",
      minute: "2-digit"
    })
  }

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">
            Customer Predictions
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            History of all churn predictions made
          </p>
        </div>
        <button
          onClick={() => { fetchData(); fetchStats() }}
          className="flex items-center gap-2 border border-gray-200
                     text-gray-600 px-3 py-2 rounded-lg
                     hover:bg-gray-50 transition text-sm"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard
            title="Total Predictions"
            value={stats.total_predictions}
            color="text-blue-600"
            icon={Brain}
          />
          <StatCard
            title="Critical Risk"
            value={stats.critical}
            color="text-red-600"
            icon={AlertTriangle}
          />
          <StatCard
            title="High Risk"
            value={stats.high}
            color="text-orange-600"
            icon={TrendingDown}
          />
          <StatCard
            title="Medium Risk"
            value={stats.medium}
            color="text-yellow-600"
            icon={AlertTriangle}
          />
          <StatCard
            title="Low Risk"
            value={stats.low}
            color="text-green-600"
            icon={CheckCircle}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* LEFT — Predictions List */}
        <div className="lg:col-span-2 space-y-4">

          {/* Search and Filter */}
          <div className="bg-white rounded-xl p-4 shadow-sm
                          border border-gray-100">
            <form onSubmit={handleSearch}
              className="flex gap-3 mb-3">
              <div className="flex-1 relative">
                <Search size={14}
                  className="absolute left-3 top-1/2
                             -translate-y-1/2 text-gray-400" />
                <input
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Search by customer ID..."
                  className="w-full pl-9 pr-4 py-2 border
                             border-gray-200 rounded-lg text-sm
                             focus:outline-none
                             focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button type="submit"
                className="bg-blue-600 text-white px-4 py-2
                           rounded-lg text-sm hover:bg-blue-700
                           transition">
                Search
              </button>
            </form>

            {/* Risk filters */}
            <div className="flex gap-2">
              {["All", "Critical", "High", "Medium", "Low"].map(r => (
                <button
                  key={r}
                  onClick={() => { setRiskFilter(r); setPage(1) }}
                  className={`px-3 py-1 rounded-full text-xs
                               font-medium transition
                    ${riskFilter === r
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Predictions Table */}
          <div className="bg-white rounded-xl shadow-sm
                          border border-gray-100 overflow-hidden">

            {loading ? (
              <div className="flex items-center justify-center h-48">
                <Loader size={20} className="animate-spin text-gray-400" />
              </div>
            ) : predictions.length === 0 ? (
              <div className="flex flex-col items-center
                              justify-center h-48 text-center">
                <Users size={32} className="text-gray-200 mb-3" />
                <p className="text-gray-400 text-sm">
                  No predictions yet
                </p>
                <p className="text-gray-300 text-xs mt-1">
                  Make predictions from the Predict Churn page
                </p>
              </div>
            ) : (
              <>
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-100">
                    <tr>
                      <th className="text-left text-xs font-medium
                                     text-gray-500 px-4 py-3">
                        Customer ID
                      </th>
                      <th className="text-left text-xs font-medium
                                     text-gray-500 px-4 py-3">
                        Risk
                      </th>
                      <th className="text-left text-xs font-medium
                                     text-gray-500 px-4 py-3">
                        Probability
                      </th>
                      <th className="text-left text-xs font-medium
                                     text-gray-500 px-4 py-3">
                        Date
                      </th>
                      <th className="text-left text-xs font-medium
                                     text-gray-500 px-4 py-3">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {predictions.map(p => (
                      <tr
                        key={p.id}
                        className={`hover:bg-gray-50 transition
                          ${selected === p.customer_id
                            ? "bg-blue-50"
                            : ""
                          }`}
                      >
                        <td className="px-4 py-3 text-sm
                                       font-medium text-gray-800">
                          {p.customer_id}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`text-xs px-2 py-1
                                            rounded-full font-medium
                            ${RISK_STYLES[p.risk_category]}`}>
                            {p.risk_category}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {(p.churn_probability * 100).toFixed(1)}%
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-400">
                          {formatDate(p.predicted_at)}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleViewCustomer(p.customer_id)}
                              className="p-1 text-blue-500
                                         hover:text-blue-700 transition"
                              title="View history"
                            >
                              <Eye size={14} />
                            </button>
                            <button
                              onClick={() => handleDelete(p.id)}
                              className="p-1 text-red-400
                                         hover:text-red-600 transition"
                              title="Delete"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {/* Pagination */}
                <div className="flex items-center justify-between
                                px-4 py-3 border-t border-gray-100">
                  <p className="text-xs text-gray-400">
                    Showing {predictions.length} of {total} predictions
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="p-1 rounded border border-gray-200
                                 disabled:opacity-50 hover:bg-gray-50
                                 transition"
                    >
                      <ChevronLeft size={14} />
                    </button>
                    <span className="text-xs text-gray-600">
                      {page} / {totalPages}
                    </span>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="p-1 rounded border border-gray-200
                                 disabled:opacity-50 hover:bg-gray-50
                                 transition"
                    >
                      <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* RIGHT — Customer Detail */}
        <div className="space-y-4">
          {!selected ? (
            <div className="bg-white rounded-xl p-6 shadow-sm
                            border border-gray-100 flex flex-col
                            items-center justify-center h-64
                            text-center">
              <Eye size={32} className="text-gray-200 mb-3" />
              <p className="text-gray-400 text-sm">
                Click the eye icon on any prediction to view
                customer history
              </p>
            </div>
          ) : detailLoading ? (
            <div className="bg-white rounded-xl p-6 shadow-sm
                            border border-gray-100 flex items-center
                            justify-center h-48">
              <Loader size={20} className="animate-spin text-gray-400" />
            </div>
          ) : customerDetail ? (
            <div className="bg-white rounded-xl p-5 shadow-sm
                            border border-gray-100">

              {/* Customer header */}
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="font-semibold text-gray-800">
                    {customerDetail.customer_id}
                  </p>
                  <p className="text-xs text-gray-400">
                    {customerDetail.total} prediction
                    {customerDetail.total !== 1 ? "s" : ""}
                  </p>
                </div>
                <div className="text-right">
                  <span className={`text-xs px-2 py-1 rounded-full
                                    font-medium
                    ${RISK_STYLES[customerDetail.latest_risk]}`}>
                    {customerDetail.latest_risk}
                  </span>
                  <p className="text-xs text-gray-400 mt-1">
                    Latest risk
                  </p>
                </div>
              </div>

              {/* Latest probability */}
              <div className="text-center py-4 bg-gray-50
                              rounded-lg mb-4">
                <p className="text-4xl font-bold text-gray-800">
                  {(customerDetail.latest_probability * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Latest churn probability
                </p>
                <p className={`text-xs font-medium mt-1
                  ${customerDetail.trend === "increasing"
                    ? "text-red-500"
                    : customerDetail.trend === "decreasing"
                    ? "text-green-500"
                    : "text-gray-400"
                  }`}>
                  {customerDetail.trend === "increasing" ? "↑ Risk increasing" :
                   customerDetail.trend === "decreasing" ? "↓ Risk decreasing" :
                   "→ Stable"}
                </p>
              </div>

              {/* Prediction history */}
              <p className="text-xs font-semibold text-gray-400
                            uppercase tracking-wide mb-3">
                Prediction History
              </p>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {customerDetail.predictions.map((p, i) => (
                  <div key={p.id}
                    className="flex items-center justify-between
                               p-2 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400">
                        #{i + 1}
                      </span>
                      <span className={`text-xs px-2 py-0.5
                                        rounded-full font-medium
                        ${RISK_STYLES[p.risk_category]}`}>
                        {p.risk_category}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium
                                       text-gray-700">
                        {(p.churn_probability * 100).toFixed(1)}%
                      </span>
                      <button
                        onClick={() => handleDelete(p.id)}
                        className="text-red-300 hover:text-red-500
                                   transition"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Top factors from latest prediction */}
              {customerDetail.predictions[0]?.feature_importances && (
                <div className="mt-4">
                  <p className="text-xs font-semibold text-gray-400
                                uppercase tracking-wide mb-2">
                    Latest Risk Factors
                  </p>
                  <div className="space-y-1">
                    {customerDetail.predictions[0]
                      .feature_importances
                      .slice(0, 3)
                      .map((f, i) => (
                        <div key={i}
                          className="flex items-center
                                     justify-between text-xs">
                          <span className="text-gray-600 capitalize">
                            {f.feature}
                          </span>
                          <span className={
                            f.impact > 0
                              ? "text-red-500"
                              : "text-green-500"
                          }>
                            {f.impact > 0 ? "↑" : "↓"}
                            {Math.abs(f.impact).toFixed(3)}
                          </span>
                        </div>
                      ))
                    }
                  </div>
                </div>
              )}

            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}