import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import {
  Users, TrendingDown, AlertTriangle,
  CheckCircle, ArrowRight, Brain,
  RefreshCw, DollarSign
} from "lucide-react"
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart,
  Pie, Cell, Legend
} from "recharts"
import { useData } from "../context/DataContext"
import API from "../services/api"

function StatCard({ title, value, subtitle, icon: Icon, color, loading }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 mb-1">{title}</p>
          {loading
            ? <div className="h-8 w-24 bg-gray-100 rounded animate-pulse mt-1" />
            : <p className={`text-3xl font-bold ${color}`}>{value}</p>
          }
          <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
        </div>
        <div className="p-2 rounded-lg bg-gray-50">
          <Icon size={20} className={color} />
        </div>
      </div>
    </div>
  )
}

const RISK_DISTRIBUTION = [
  { name: "Low Risk",      value: 45, color: "#22c55e" },
  { name: "Medium Risk",   value: 28, color: "#f59e0b" },
  { name: "High Risk",     value: 18, color: "#f97316" },
  { name: "Critical Risk", value: 9,  color: "#ef4444" },
]

export default function Dashboard() {
  const navigate          = useNavigate()
  const { summary, datasetInfo, loading, refreshData } = useData()
  const [contractData,  setContractData]  = useState([])
  const [internetData,  setInternetData]  = useState([])
  const [chartsLoading, setChartsLoading] = useState(true)

  useEffect(() => {
    fetchChartData()
  }, [])

  const fetchChartData = async () => {
    setChartsLoading(true)
    try {
      const [contractRes, internetRes] = await Promise.all([
        API.get("/analytics/churn-by-contract"),
        API.get("/analytics/churn-by-internet"),
      ])
      setContractData(contractRes.data || [])
      setInternetData(internetRes.data || [])
    } catch (err) {
      console.error("Chart data error:", err)
    } finally {
      setChartsLoading(false)
    }
  }

  const handleRefresh = async () => {
    await refreshData()
    await fetchChartData()
  }

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>
          <p className="text-gray-500 text-sm mt-1">
            {datasetInfo?.filename
              ? `Dataset: ${datasetInfo.filename}`
              : "Customer churn overview"
            }
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 border border-gray-200
                       text-gray-600 px-3 py-2 rounded-lg
                       hover:bg-gray-50 transition text-sm"
          >
            <RefreshCw size={14} /> Refresh
          </button>
          <button
            onClick={() => navigate("/predict")}
            className="flex items-center gap-2 bg-blue-600 text-white
                       px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm"
          >
            <Brain size={16} /> Predict Customer
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Customers"
          value={summary?.total_customers?.toLocaleString() || "0"}
          subtitle={`${datasetInfo?.filename || "No dataset"}`}
          icon={Users}
          color="text-blue-600"
          loading={loading}
        />
        <StatCard
          title="Churn Rate"
          value={`${summary?.churn_rate || 0}%`}
          subtitle={`${summary?.churned_customers?.toLocaleString() || 0} customers churned`}
          icon={TrendingDown}
          color="text-red-500"
          loading={loading}
        />
        <StatCard
          title="Avg Monthly Charges"
          value={`$${summary?.avg_monthly_charges || 0}`}
          subtitle={`Churners pay $${summary?.churner_avg_monthly || 0} avg`}
          icon={DollarSign}
          color="text-orange-500"
          loading={loading}
        />
        <StatCard
          title="Retained Customers"
          value={summary?.retained_customers?.toLocaleString() || "0"}
          subtitle={`${(100 - (summary?.churn_rate || 0)).toFixed(1)}% retention rate`}
          icon={CheckCircle}
          color="text-green-500"
          loading={loading}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Churn by Contract */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-4">
            Churn Rate by Contract Type
          </h3>
          {chartsLoading
            ? <div className="h-48 bg-gray-50 rounded animate-pulse" />
            : (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={contractData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} tickLine={false} unit="%" />
                  <Tooltip
                    formatter={(v) => [`${v}%`, "Churn Rate"]}
                    contentStyle={{ borderRadius: 8 }}
                  />
                  <Bar
                    dataKey="churnRate"
                    fill="#3b82f6"
                    radius={[4, 4, 0, 0]}
                    name="Churn Rate"
                  />
                </BarChart>
              </ResponsiveContainer>
            )
          }
        </div>

        {/* Risk Distribution */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-4">
            Customer Risk Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={RISK_DISTRIBUTION}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="value"
              >
                {RISK_DISTRIBUTION.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => [`${v}%`, "Customers"]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Churn by Internet Service */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-700 mb-4">
          Churn Rate by Internet Service
        </h3>
        {chartsLoading
          ? <div className="h-24 bg-gray-50 rounded animate-pulse" />
          : (
            <div className="space-y-3">
              {internetData.map((item) => (
                <div key={item.name} className="flex items-center gap-4">
                  <span className="text-sm text-gray-600 w-32 shrink-0">
                    {item.name}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-3">
                    <div
                      className="h-3 rounded-full transition-all duration-700"
                      style={{
                        width:           `${item.churnRate}%`,
                        backgroundColor:
                          item.churnRate > 30 ? "#ef4444" :
                          item.churnRate > 15 ? "#f59e0b" : "#22c55e"
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-700 w-12 text-right">
                    {item.churnRate}%
                  </span>
                </div>
              ))}
            </div>
          )
        }
      </div>

      {/* Revenue at Risk */}
      {summary?.revenue_at_risk > 0 && (
        <div className="bg-gradient-to-r from-red-500 to-red-600
                        rounded-xl p-5 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-100 text-sm">Monthly Revenue at Risk</p>
              <p className="text-4xl font-bold mt-1">
                ${summary.revenue_at_risk.toLocaleString()}
              </p>
              <p className="text-red-100 text-sm mt-1">
                From {summary.churned_customers} churned customers
              </p>
            </div>
            <div className="text-right">
              <button
                onClick={() => navigate("/retention")}
                className="flex items-center gap-2 bg-white text-red-600
                           px-4 py-2 rounded-lg hover:bg-red-50
                           transition text-sm font-medium"
              >
                View At-Risk Customers
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CTA */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700
                      rounded-xl p-6 text-white">
        <h3 className="font-semibold text-lg mb-2">
          Ready to predict customer churn?
        </h3>
        <p className="text-blue-100 text-sm mb-4">
          Enter customer data and get instant AI-powered churn probability
          with explainable insights and retention strategies.
        </p>
        <button
          onClick={() => navigate("/predict")}
          className="flex items-center gap-2 bg-white text-blue-600
                     px-4 py-2 rounded-lg hover:bg-blue-50
                     transition text-sm font-medium"
        >
          Start Prediction <ArrowRight size={16} />
        </button>
      </div>

    </div>
  )
}