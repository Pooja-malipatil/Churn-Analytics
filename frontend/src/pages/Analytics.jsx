import { useState, useEffect } from "react"
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart,
  Pie, Cell, Legend, LineChart, Line
} from "recharts"
import {
  TrendingDown, Users, DollarSign,
  AlertTriangle, Download, Loader
} from "lucide-react"
import { useData } from "../context/DataContext"
import API from "../services/api"
import { downloadAnalyticsReport } from "../services/api"

function InsightCard({ icon: Icon, color, title, value, description, loading }) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon size={16} className="text-white" />
        </div>
        <p className="text-sm font-medium text-gray-700">{title}</p>
      </div>
      {loading
        ? <div className="h-8 w-20 bg-gray-100 rounded animate-pulse" />
        : <p className="text-2xl font-bold text-gray-800">{value}</p>
      }
      <p className="text-xs text-gray-400 mt-1">{description}</p>
    </div>
  )
}

function Section({ title, subtitle, children }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="mb-4">
        <h3 className="font-semibold text-gray-700">{title}</h3>
        {subtitle && (
          <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>
        )}
      </div>
      {children}
    </div>
  )
}

function LoadingChart() {
  return (
    <div className="h-64 bg-gray-50 rounded-lg animate-pulse
                    flex items-center justify-center">
      <p className="text-gray-300 text-sm">Loading chart data...</p>
    </div>
  )
}

export default function Analytics() {
  const [activeTab,     setActiveTab]     = useState("overview")
  const [reportLoading, setReportLoading] = useState(false)
  const { summary, loading: summaryLoading } = useData()

  const [contractData,  setContractData]  = useState([])
  const [tenureData,    setTenureData]    = useState([])
  const [internetData,  setInternetData]  = useState([])
  const [paymentData,   setPaymentData]   = useState([])
  const [chargesData,   setChargesData]   = useState([])
  const [serviceData,   setServiceData]   = useState([])
  const [chartsLoading, setChartsLoading] = useState(true)

  useEffect(() => {
    fetchAllCharts()
  }, [])

  const fetchAllCharts = async () => {
    setChartsLoading(true)
    try {
      const [
        contractRes, tenureRes,  internetRes,
        paymentRes,  chargesRes, serviceRes
      ] = await Promise.all([
        API.get("/analytics/churn-by-contract"),
        API.get("/analytics/churn-by-tenure"),
        API.get("/analytics/churn-by-internet"),
        API.get("/analytics/churn-by-payment"),
        API.get("/analytics/churn-by-charges"),
        API.get("/analytics/service-impact"),
      ])
      setContractData(contractRes.data || [])
      setTenureData(tenureRes.data     || [])
      setInternetData(internetRes.data || [])
      setPaymentData(paymentRes.data   || [])
      setChargesData(chargesRes.data   || [])
      setServiceData(serviceRes.data   || [])
    } catch (err) {
      console.error("Analytics error:", err)
    } finally {
      setChartsLoading(false)
    }
  }

  const handleDownloadReport = async () => {
    setReportLoading(true)
    try {
      await downloadAnalyticsReport()
    } catch (err) {
      console.error("Report error:", err)
      alert("Failed to generate report. Please try again.")
    } finally {
      setReportLoading(false)
    }
  }

  const tabs = [
    { id: "overview",  label: "Overview"          },
    { id: "contract",  label: "Contract Analysis" },
    { id: "services",  label: "Service Impact"    },
    { id: "financial", label: "Financial Analysis"},
  ]

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Analytics</h2>
          <p className="text-gray-500 text-sm mt-1">
            Real-time insights from your active dataset
          </p>
        </div>
        <button
          onClick={handleDownloadReport}
          disabled={reportLoading}
          className="flex items-center gap-2 bg-blue-600 text-white
                     px-4 py-2 rounded-lg hover:bg-blue-700
                     transition text-sm disabled:opacity-50"
        >
          {reportLoading
            ? <><Loader size={16} className="animate-spin" /> Generating...</>
            : <><Download size={16} /> Download PDF Report</>
          }
        </button>
      </div>

      {/* Key Insights */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <InsightCard
          icon={Users}
          color="bg-blue-500"
          title="Total Customers"
          value={summary?.total_customers?.toLocaleString() || "0"}
          description="In active dataset"
          loading={summaryLoading}
        />
        <InsightCard
          icon={TrendingDown}
          color="bg-red-500"
          title="Churn Rate"
          value={`${summary?.churn_rate || 0}%`}
          description={`${summary?.churned_customers || 0} churned`}
          loading={summaryLoading}
        />
        <InsightCard
          icon={DollarSign}
          color="bg-green-500"
          title="Avg Monthly"
          value={`$${summary?.avg_monthly_charges || 0}`}
          description={`Churners: $${summary?.churner_avg_monthly || 0}`}
          loading={summaryLoading}
        />
        <InsightCard
          icon={AlertTriangle}
          color="bg-orange-500"
          title="Revenue at Risk"
          value={`$${summary?.revenue_at_risk?.toLocaleString() || 0}`}
          description="Monthly from churners"
          loading={summaryLoading}
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition
              ${activeTab === tab.id
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <Section
            title="Churn Rate by Contract Type"
            subtitle="Contract type is the strongest predictor of churn"
          >
            {chartsLoading ? <LoadingChart /> : (
              <>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={contractData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} tickLine={false} />
                    <YAxis tick={{ fontSize: 11 }} tickLine={false} />
                    <Tooltip contentStyle={{ borderRadius: 8 }} />
                    <Legend />
                    <Bar dataKey="churned"  name="Churned"
                      fill="#ef4444" radius={[4,4,0,0]} />
                    <Bar dataKey="retained" name="Retained"
                      fill="#22c55e" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
                {contractData[0] && (
                  <div className="mt-3 p-3 bg-red-50 rounded-lg
                                  border border-red-100">
                    <p className="text-xs text-red-600">
                      Highest churn: <strong>{contractData[0]?.name}</strong> at{" "}
                      <strong>{contractData[0]?.churnRate}%</strong>
                    </p>
                  </div>
                )}
              </>
            )}
          </Section>

          <Section
            title="Churn Rate by Customer Tenure"
            subtitle="New customers are most at risk"
          >
            {chartsLoading ? <LoadingChart /> : (
              <>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={tenureData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="tenure" tick={{ fontSize: 10 }}
                      tickLine={false} />
                    <YAxis tick={{ fontSize: 11 }} tickLine={false} unit="%" />
                    <Tooltip
                      formatter={(v) => [`${v}%`, "Churn Rate"]}
                      contentStyle={{ borderRadius: 8 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="churnRate"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: "#3b82f6", r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
                {tenureData[0] && (
                  <div className="mt-3 p-3 bg-blue-50 rounded-lg
                                  border border-blue-100">
                    <p className="text-xs text-blue-600">
                      Highest risk: customers in{" "}
                      <strong>{tenureData[0]?.tenure}</strong> at{" "}
                      <strong>{tenureData[0]?.churnRate}%</strong>
                    </p>
                  </div>
                )}
              </>
            )}
          </Section>
        </div>
      )}

      {/* CONTRACT TAB */}
      {activeTab === "contract" && (
        <div className="space-y-6">
          <Section
            title="Churn Rate by Contract Type"
            subtitle="Clear correlation between contract length and loyalty"
          >
            {chartsLoading ? <LoadingChart /> : (
              <div className="space-y-4">
                {contractData.map((item) => (
                  <div key={item.name}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-700">
                        {item.name}
                      </span>
                      <span className="text-sm font-medium text-gray-700">
                        {item.churnRate}% churn
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-4">
                      <div
                        className="h-4 rounded-full transition-all duration-700"
                        style={{
                          width: `${item.churnRate}%`,
                          backgroundColor:
                            item.churnRate > 30 ? "#ef4444" :
                            item.churnRate > 15 ? "#f59e0b" : "#22c55e"
                        }}
                      />
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {item.total?.toLocaleString()} customers
                    </p>
                  </div>
                ))}
              </div>
            )}
          </Section>

          <Section
            title="Churn Rate by Payment Method"
            subtitle="Payment method impacts churn significantly"
          >
            {chartsLoading ? <LoadingChart /> : (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={paymentData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" tick={{ fontSize: 11 }} unit="%" />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fontSize: 11 }}
                    width={130}
                  />
                  <Tooltip formatter={(v) => [`${v}%`, "Churn Rate"]} />
                  <Bar dataKey="churnRate" fill="#3b82f6" radius={[0,4,4,0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Section>
        </div>
      )}

      {/* SERVICES TAB */}
      {activeTab === "services" && (
        <div className="space-y-6">
          <Section
            title="Impact of Services on Churn Rate"
            subtitle="Customers with security and support churn less"
          >
            {chartsLoading ? <LoadingChart /> : (
              <>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={serviceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="service" tick={{ fontSize: 11 }}
                      tickLine={false} />
                    <YAxis tick={{ fontSize: 11 }} tickLine={false} unit="%" />
                    <Tooltip
                      formatter={(v) => [`${v}%`, "Churn Rate"]}
                      contentStyle={{ borderRadius: 8 }}
                    />
                    <Legend />
                    <Bar dataKey="withService" name="With Service"
                      fill="#22c55e" radius={[4,4,0,0]} />
                    <Bar dataKey="withoutService" name="Without Service"
                      fill="#ef4444" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-3 p-3 bg-green-50 rounded-lg
                                border border-green-100">
                  <p className="text-xs text-green-700">
                    Adding security and support services significantly
                    reduces churn
                  </p>
                </div>
              </>
            )}
          </Section>

          <Section
            title="Churn Rate by Internet Service"
            subtitle="Service type impacts customer loyalty"
          >
            {chartsLoading ? <LoadingChart /> : (
              <div className="space-y-3">
                {internetData.map((item) => (
                  <div key={item.name}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-700">
                        {item.name}
                      </span>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-gray-400">
                          {item.customers?.toLocaleString()} customers
                        </span>
                        <span className="text-sm font-medium text-gray-700">
                          {item.churnRate}%
                        </span>
                      </div>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-3">
                      <div
                        className="h-3 rounded-full"
                        style={{
                          width: `${item.churnRate}%`,
                          backgroundColor:
                            item.churnRate > 30 ? "#ef4444" :
                            item.churnRate > 15 ? "#f59e0b" : "#22c55e"
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Section>
        </div>
      )}

      {/* FINANCIAL TAB */}
      {activeTab === "financial" && (
        <div className="space-y-6">
          <Section
            title="Churn Rate by Monthly Charges"
            subtitle="Higher charges strongly correlate with churn"
          >
            {chartsLoading ? <LoadingChart /> : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chargesData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="range" tick={{ fontSize: 11 }}
                    tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} tickLine={false} unit="%" />
                  <Tooltip formatter={(v) => [`${v}%`, "Churn Rate"]} />
                  <Bar dataKey="churnRate" fill="#ef4444"
                    radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Section>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-red-50 rounded-xl p-4 border border-red-100">
              <p className="text-sm text-red-600 font-medium">
                Avg Charges — Churners
              </p>
              <p className="text-3xl font-bold text-red-700 mt-1">
                ${summary?.churner_avg_monthly || 0}
              </p>
              <p className="text-xs text-red-400 mt-1">per month</p>
            </div>
            <div className="bg-green-50 rounded-xl p-4 border border-green-100">
              <p className="text-sm text-green-600 font-medium">
                Avg Charges — Retained
              </p>
              <p className="text-3xl font-bold text-green-700 mt-1">
                ${summary?.retained_avg_monthly || 0}
              </p>
              <p className="text-xs text-green-400 mt-1">per month</p>
            </div>
            <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
              <p className="text-sm text-blue-600 font-medium">
                Revenue at Risk
              </p>
              <p className="text-3xl font-bold text-blue-700 mt-1">
                ${summary?.revenue_at_risk?.toLocaleString() || 0}
              </p>
              <p className="text-xs text-blue-400 mt-1">
                monthly from churners
              </p>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}