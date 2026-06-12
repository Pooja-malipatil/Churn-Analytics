import { useState, useEffect } from "react"
import {
  predictChurn,
  downloadCustomerReport,
  getModelFeatures
} from "../services/api"
import {
  Brain, CheckCircle, TrendingDown,
  Lightbulb, Loader, Download,
  RefreshCw, Info
} from "lucide-react"

const RISK_COLORS = {
  Low:      { bg: "bg-green-50",  text: "text-green-700",  border: "border-green-200",  badge: "bg-green-100"  },
  Medium:   { bg: "bg-yellow-50", text: "text-yellow-700", border: "border-yellow-200", badge: "bg-yellow-100" },
  High:     { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200", badge: "bg-orange-100" },
  Critical: { bg: "bg-red-50",    text: "text-red-700",    border: "border-red-200",    badge: "bg-red-100"    },
}

export default function PredictCustomer() {
  const [features,      setFeatures]      = useState([])
  const [datasetInfo,   setDatasetInfo]   = useState(null)
  const [loadingFields, setLoadingFields] = useState(true)
  const [formValues,    setFormValues]    = useState({})
  const [customerId,    setCustomerId]    = useState("")
  const [result,        setResult]        = useState(null)
  const [loading,       setLoading]       = useState(false)
  const [error,         setError]         = useState(null)
  const [reportLoading, setReportLoading] = useState(false)

  useEffect(() => {
    fetchFeatures()
  }, [])

  const fetchFeatures = async () => {
    setLoadingFields(true)
    try {
      const data = await getModelFeatures()

      // Clean all feature values to plain strings
      const cleanFeatures = (data.features || []).map(f => ({
        ...f,
        values: (f.values || []).map(v => String(v)),
      }))

      setFeatures(cleanFeatures)
      setDatasetInfo({
        total_rows: data.total_rows,
        churn_rate: data.churn_rate,
      })

      // Set defaults
      const defaults = {}
      cleanFeatures.forEach(f => {
        if (f.type === "numeric") {
          defaults[f.model_name] = f.stats?.mean ?? 0
        } else if (f.type === "categorical") {
          defaults[f.model_name] = String(f.values?.[0] ?? "")
        } else if (f.type === "binary") {
          defaults[f.model_name] = false
        }
      })
      setFormValues(defaults)

    } catch (err) {
      console.error("Feature fetch error:", err)
    } finally {
      setLoadingFields(false)
    }
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormValues(prev => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }))
  }

  const handleSubmit = async (e) => {
  e.preventDefault()
  setLoading(true)
  setError(null)
  setResult(null)

  try {
    // Force all values to correct types
    const tenure   = parseFloat(formValues.tenure_months)
    const monthly  = parseFloat(formValues.monthly_charges)
    const total    = parseFloat(formValues.total_charges)
    const tickets  = parseInt(formValues.num_support_tickets)
    const contract = formValues.contract_type
    const internet = formValues.internet_service
    const payment  = formValues.payment_method

    const payload = {
      customer_id:         customerId || "CUST_PRED",
      tenure_months:       isNaN(tenure)  ? 0   : tenure,
      monthly_charges:     isNaN(monthly) ? 0.0 : monthly,
      total_charges:       isNaN(total)   ? 0.0 : total,
      num_support_tickets: isNaN(tickets) ? 0   : tickets,
      contract_type:       typeof contract === "string" ? contract : String(contract ?? "Month-to-month"),
      internet_service:    typeof internet === "string" ? internet : String(internet ?? "DSL"),
      payment_method:      typeof payment  === "string" ? payment  : String(payment  ?? "Electronic check"),
      online_security:     false,
      tech_support:        false,
      streaming_tv:        false,
      streaming_movies:    false,
      phone_service:       true,
      multiple_lines:      false,
    }

    console.log("Payload:", JSON.stringify(payload))
    const data = await predictChurn(payload)
    setResult(data)

  } catch (err) {
    setError(err.message)
  } finally {
    setLoading(false)
  }
}

  const handleDownloadReport = async () => {
    if (!result) return
    setReportLoading(true)
    try {
      await downloadCustomerReport(result)
    } catch (err) {
      alert("Failed to generate report.")
    } finally {
      setReportLoading(false)
    }
  }

  const numericFeatures     = features.filter(f => f.type === "numeric")
  const categoricalFeatures = features.filter(f => f.type === "categorical")
  const colors              = result ? RISK_COLORS[result.risk_category] : null

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">
            Predict Customer Churn
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            {datasetInfo
              ? `${datasetInfo.total_rows?.toLocaleString()} customers · ${datasetInfo.churn_rate}% churn rate`
              : "Loading..."
            }
          </p>
        </div>
        <button
          onClick={fetchFeatures}
          className="flex items-center gap-2 border border-gray-200
                     text-gray-600 px-3 py-2 rounded-lg
                     hover:bg-gray-50 transition text-sm"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {loadingFields ? (
        <div className="flex items-center justify-center h-48">
          <div className="flex items-center gap-3 text-gray-500">
            <Loader size={20} className="animate-spin" />
            <span>Loading prediction fields...</span>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* FORM */}
          <div className="bg-white rounded-xl p-6 shadow-sm
                          border border-gray-100">

            {/* Info */}
            <div className="flex items-start gap-2 p-3 bg-blue-50
                            rounded-lg border border-blue-100 mb-5">
              <Info size={14} className="text-blue-500 shrink-0 mt-0.5" />
              <p className="text-xs text-blue-600">
                Fill in the customer details below.
                Default values are based on your dataset averages.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">

              {/* Customer ID */}
              <div>
                <label className="block text-sm font-medium
                                  text-gray-700 mb-1">
                  Customer ID
                </label>
                <input
                  value={customerId}
                  onChange={e => setCustomerId(e.target.value)}
                  placeholder="e.g. CUST_001"
                  className="w-full border border-gray-200 rounded-lg
                             px-3 py-2 text-sm focus:outline-none
                             focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* NUMERIC FIELDS */}
              {numericFeatures.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-400
                                uppercase tracking-wide mb-3">
                    Key Metrics
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    {numericFeatures.map(feature => (
                      <div key={feature.model_name}>
                        <label className="block text-sm font-medium
                                          text-gray-700 mb-1">
                          {feature.label}
                          {feature.required && (
                            <span className="text-red-400 ml-1">*</span>
                          )}
                        </label>
                        <input
                          name={feature.model_name}
                          type="number"
                          value={formValues[feature.model_name] ?? ""}
                          onChange={handleChange}
                          step="any"
                          placeholder={String(feature.stats?.mean ?? 0)}
                          className="w-full border border-gray-200
                                     rounded-lg px-3 py-2 text-sm
                                     focus:outline-none
                                     focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="text-xs text-gray-400 mt-0.5">
                          {feature.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* CATEGORICAL FIELDS */}
              {categoricalFeatures.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-400
                                uppercase tracking-wide mb-3">
                    Plan Details
                    <span className="text-gray-300 font-normal
                                     ml-2 normal-case">
                      (optional)
                    </span>
                  </p>
                  <div className="space-y-3">
                    {categoricalFeatures.map(feature => (
                      <div key={feature.model_name}>
                        <label className="block text-sm font-medium
                                          text-gray-700 mb-1">
                          {feature.label}
                        </label>

                        {feature.values && feature.values.length > 0 ? (
                          <select
                          name={feature.model_name}
                          value={
                          formValues[feature.model_name] !== undefined &&
                          formValues[feature.model_name] !== null
                          ? String(formValues[feature.model_name])
                          : String(feature.values[0])
                          }
                        onChange={handleChange}
                        className="w-full border border-gray-200
                        rounded-lg px-3 py-2 text-sm
                        focus:outline-none
                        focus:ring-2 focus:ring-blue-500"
                        >
                        {feature.values.map((val, i) => {
                        const strVal = String(val)
                        return (
                        <option key={i} value={strVal}>
                        {strVal}
                        </option>
                        )
                      })}
                    </select>
                        ) : (
                          <input
                            name={feature.model_name}
                            type="text"
                            value={String(formValues[feature.model_name] ?? "")}
                            onChange={handleChange}
                            placeholder={`Enter ${feature.label}`}
                            className="w-full border border-gray-200
                                       rounded-lg px-3 py-2 text-sm
                                       focus:outline-none
                                       focus:ring-2 focus:ring-blue-500"
                          />
                        )}
                        <p className="text-xs text-gray-400 mt-0.5">
                          {feature.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="bg-red-50 border border-red-200
                                rounded-lg p-3">
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2.5
                           rounded-lg hover:bg-blue-700 transition
                           font-medium text-sm flex items-center
                           justify-center gap-2 disabled:opacity-50
                           disabled:cursor-not-allowed"
              >
                {loading
                  ? <><Loader size={16} className="animate-spin" />
                      Analyzing...</>
                  : <><Brain size={16} /> Predict Churn Risk</>
                }
              </button>

            </form>
          </div>

          {/* RESULTS */}
          <div className="space-y-4">

            {!result && !loading && (
              <div className="bg-white rounded-xl p-6 shadow-sm
                              border border-gray-100 flex flex-col
                              items-center justify-center h-64
                              text-center">
                <Brain size={40} className="text-gray-300 mb-3" />
                <p className="text-gray-400 text-sm">
                  Fill in customer details and click predict
                </p>
                <p className="text-gray-300 text-xs mt-1">
                  The AI uses {features.length} key factors
                </p>
              </div>
            )}

            {result && colors && (
              <>
                {/* Risk Score */}
                <div className={`rounded-xl p-6 shadow-sm border
                                 ${colors.bg} ${colors.border}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className={`font-semibold ${colors.text}`}>
                      Churn Risk Analysis
                    </h3>
                    <span className={`text-xs px-3 py-1 rounded-full
                                      font-medium ${colors.badge}
                                      ${colors.text}`}>
                      {result.risk_category} Risk
                    </span>
                  </div>
                  <div className="text-center py-4">
                    <p className={`text-6xl font-bold ${colors.text}`}>
                      {(result.churn_probability * 100).toFixed(1)}%
                    </p>
                    <p className="text-gray-500 text-sm mt-2">
                      Probability of churning
                    </p>
                  </div>
                  <div className="bg-white bg-opacity-60
                                  rounded-full h-3 mt-2">
                    <div
                      className="h-3 rounded-full transition-all
                                 duration-1000"
                      style={{
                        width: `${result.churn_probability * 100}%`,
                        backgroundColor:
                          result.risk_category === "Critical" ? "#ef4444" :
                          result.risk_category === "High"     ? "#f97316" :
                          result.risk_category === "Medium"   ? "#f59e0b" :
                          "#22c55e"
                      }}
                    />
                  </div>
                  <p className="text-sm text-gray-600 mt-3">
                    {result.explanation}
                  </p>
                </div>

                {/* Top Risk Factors */}
                <div className="bg-white rounded-xl p-5 shadow-sm
                                border border-gray-100">
                  <h3 className="font-semibold text-gray-700 mb-3
                                 flex items-center gap-2">
                    <TrendingDown size={16} className="text-red-500" />
                    Top Risk Factors
                  </h3>
                  <div className="space-y-2">
                    {result.top_risk_factors?.map((factor, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <span className="text-xs text-gray-500 w-5">
                          {i + 1}.
                        </span>
                        <span className="text-sm text-gray-700
                                         flex-1 capitalize">
                          {factor.feature}
                        </span>
                        <span className={`text-xs font-medium
                                          px-2 py-0.5 rounded
                          ${factor.impact > 0
                            ? "bg-red-50 text-red-600"
                            : "bg-green-50 text-green-600"
                          }`}>
                          {factor.impact > 0 ? "↑ Risk" : "↓ Risk"}
                        </span>
                        <span className="text-xs text-gray-400
                                         w-14 text-right">
                          {Math.abs(factor.impact).toFixed(3)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Retention Strategies */}
                <div className="bg-white rounded-xl p-5 shadow-sm
                                border border-gray-100">
                  <h3 className="font-semibold text-gray-700 mb-3
                                 flex items-center gap-2">
                    <Lightbulb size={16} className="text-yellow-500" />
                    Retention Strategies
                  </h3>
                  <div className="space-y-2">
                    {result.retention_strategies?.map((strategy, i) => (
                      <div key={i}
                        className="flex items-start gap-2 p-2
                                   bg-gray-50 rounded-lg">
                        <CheckCircle size={14}
                          className="text-green-500 mt-0.5 shrink-0" />
                        <p className="text-sm text-gray-600">
                          {strategy}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Download Report */}
                <div className="bg-white rounded-xl p-4 shadow-sm
                                border border-gray-100">
                  <button
                    onClick={handleDownloadReport}
                    disabled={reportLoading}
                    className="w-full flex items-center justify-center
                               gap-2 bg-green-600 text-white py-2.5
                               rounded-lg hover:bg-green-700 transition
                               font-medium text-sm disabled:opacity-50"
                  >
                    {reportLoading
                      ? <><Loader size={16} className="animate-spin" />
                          Generating PDF...</>
                      : <><Download size={16} />
                          Download Customer Report</>
                    }
                  </button>
                  <p className="text-xs text-gray-400 text-center mt-2">
                    Includes risk analysis and retention strategies
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}