import { useRef, useState } from "react"
import {
  Upload, FileText, CheckCircle,
  AlertTriangle, TrendingUp,
  Loader, X, ArrowRight, Database
} from "lucide-react"
import API from "../services/api"
import { useData } from "../context/DataContext"

export default function UploadDataset() {
  const {
    uploadStep,     setUploadStep,
    uploadResult,   setUploadResult,
    trainingStatus, setTrainingStatus,
    uploadedFile,   setUploadedFile,
    isPolling,
    startPolling,
    resetUpload,
    datasetInfo,
  } = useData()

  const [error,    setError]    = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploading,setUploading]= useState(false)
  const [mapping,  setMapping]  = useState({
    churn_col: "", churn_yes_value: ""
  })

  const fileInputRef = useRef(null)

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return
    if (!selectedFile.name.endsWith(".csv")) {
      setError("Please select a CSV file")
      return
    }
    setUploadedFile(selectedFile)
    setError(null)
    setUploadResult(null)
    setTrainingStatus(null)
    setUploadStep("upload")
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    handleFileSelect(e.dataTransfer.files[0])
  }

  const handleUpload = async () => {
    if (!uploadedFile) return
    setUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append("file", uploadedFile)

      const result = await API.post("/upload/dataset", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      })

      setUploadResult(result)
      setUploadStep("mapping")

      // Auto detect churn column
      const cols      = result.columns || []
      const autoChurn = [
        "Churn", "churned", "churn",
        "is_churned", "left", "cancelled"
      ].find(c => cols.includes(c)) || ""

      setMapping({ churn_col: autoChurn, churn_yes_value: "" })

    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const handleStartTraining = async () => {
    if (!mapping.churn_col || !mapping.churn_yes_value) {
      setError("Please select the churn column and churned value")
      return
    }
    setError(null)
    setUploadStep("training")
    setTrainingStatus({
      is_training: true,
      progress:    0,
      message:     "Starting training...",
    })

    try {
      await API.post("/upload/train", mapping)
      startPolling()
    } catch (err) {
      setError(err.message)
      setUploadStep("mapping")
    }
  }

  const churnColValues =
    uploadResult?.sample_values?.[mapping.churn_col] || []

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">
            Upload Dataset
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            Upload any CSV — machine auto-detects all columns
          </p>
        </div>
        {uploadStep !== "upload" && (
          <button
            onClick={resetUpload}
            className="text-sm text-gray-500 border border-gray-200
                       px-3 py-1.5 rounded-lg hover:bg-gray-50 transition"
          >
            Start over
          </button>
        )}
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {[
          { id: "upload",   label: "1. Upload File"  },
          { id: "mapping",  label: "2. Select Churn" },
          { id: "training", label: "3. Train Model"  },
        ].map((s, i) => (
          <div key={s.id} className="flex items-center gap-2">
            <div className={`
              px-3 py-1.5 rounded-full text-xs font-medium transition
              ${uploadStep === s.id
                ? "bg-blue-600 text-white"
                : uploadStep === "training" ||
                  (uploadStep === "mapping" && i === 0)
                ? "bg-green-100 text-green-700"
                : "bg-gray-100 text-gray-500"
              }
            `}>
              {s.label}
            </div>
            {i < 2 && (
              <ArrowRight size={14} className="text-gray-300" />
            )}
          </div>
        ))}
      </div>

      {/* Current Active Dataset */}
      {datasetInfo && datasetInfo.rows && (
        <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
          <div className="flex items-center gap-2 mb-2">
            <Database size={16} className="text-blue-600" />
            <p className="text-sm font-medium text-blue-700">
              Current Active Dataset
            </p>
          </div>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-blue-500">File</p>
              <p className="text-sm font-medium text-blue-800 truncate">
                {datasetInfo.filename}
              </p>
            </div>
            <div>
              <p className="text-xs text-blue-500">Rows</p>
              <p className="text-sm font-medium text-blue-800">
                {datasetInfo.rows?.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-blue-500">Columns</p>
              <p className="text-sm font-medium text-blue-800">
                {datasetInfo.num_columns}
              </p>
            </div>
            <div>
              <p className="text-xs text-blue-500">Churn Rate</p>
              <p className="text-sm font-medium text-blue-800">
                {datasetInfo.churn_rate}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* STEP 1 — UPLOAD */}
      {uploadStep === "upload" && (
        <div className="bg-white rounded-xl p-6 shadow-sm
                        border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-4">
            Upload CSV File
          </h3>

          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`
              border-2 border-dashed rounded-xl p-10
              flex flex-col items-center justify-center
              cursor-pointer transition-all duration-200
              ${dragOver
                ? "border-blue-500 bg-blue-50"
                : "border-gray-200 hover:border-blue-300 hover:bg-gray-50"
              }
            `}
          >
            <Upload
              size={36}
              className={dragOver ? "text-blue-500" : "text-gray-300"}
            />
            <p className="text-sm font-medium text-gray-600 mt-3">
              Drop CSV file here or click to browse
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Works with ANY CSV format
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => handleFileSelect(e.target.files[0])}
            />
          </div>

          {uploadedFile && (
            <div className="mt-4 flex items-center gap-3 p-3
                            bg-gray-50 rounded-lg border border-gray-200">
              <FileText size={20} className="text-blue-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700 truncate">
                  {uploadedFile.name}
                </p>
                <p className="text-xs text-gray-400">
                  {(uploadedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setUploadedFile(null)
                }}
                className="text-gray-400 hover:text-red-500 transition"
              >
                <X size={16} />
              </button>
            </div>
          )}

          {error && (
            <div className="mt-4 flex items-start gap-2 p-3
                            bg-red-50 rounded-lg border border-red-200">
              <AlertTriangle size={16}
                className="text-red-500 shrink-0 mt-0.5" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!uploadedFile || uploading}
            className="w-full mt-4 bg-blue-600 text-white py-2.5
                       rounded-lg hover:bg-blue-700 transition
                       font-medium text-sm flex items-center
                       justify-center gap-2 disabled:opacity-50
                       disabled:cursor-not-allowed"
          >
            {uploading
              ? <><Loader size={16} className="animate-spin" /> Uploading...</>
              : <><Upload size={16} /> Upload CSV</>
            }
          </button>
        </div>
      )}

      {/* STEP 2 — SELECT CHURN COLUMN */}
      {uploadStep === "mapping" && uploadResult && (
        <div className="bg-white rounded-xl p-6 shadow-sm
                        border border-gray-100">

          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-700">
              Identify Churn Column
            </h3>
            <div className="flex items-center gap-2 text-xs
                            text-green-600 bg-green-50 px-3 py-1
                            rounded-full border border-green-200">
              <CheckCircle size={12} />
              {uploadResult.num_rows?.toLocaleString()} rows ready
            </div>
          </div>

          <p className="text-sm text-gray-500 mb-4">
            Found <strong>{uploadResult.num_columns} columns</strong>.
            Just tell us which one shows if a customer churned —
            we handle the rest automatically!
          </p>

          {/* Clickable column badges */}
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500 mb-2">
              Click a column to select it:
            </p>
            <div className="flex flex-wrap gap-1">
              {uploadResult.columns?.map((col, i) => (
                <span
                  key={i}
                  onClick={() => setMapping(p => ({
                    ...p, churn_col: col, churn_yes_value: ""
                  }))}
                  className={`
                    text-xs px-2 py-1 rounded-full cursor-pointer
                    transition border
                    ${mapping.churn_col === col
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-blue-700 border-blue-200 hover:bg-blue-50"
                    }
                  `}
                >
                  {col}
                </span>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
              <p className="text-sm font-medium text-blue-700 mb-4">
                Just 2 things needed:
              </p>

              <div className="mb-4">
                <label className="block text-sm font-medium
                                  text-gray-700 mb-1">
                  1. Which column shows if customer churned?
                  <span className="text-red-500"> *</span>
                </label>
                <select
                  value={mapping.churn_col}
                  onChange={(e) => setMapping(p => ({
                    ...p,
                    churn_col:       e.target.value,
                    churn_yes_value: ""
                  }))}
                  className="w-full border border-gray-200 rounded-lg
                             px-3 py-2 text-sm focus:outline-none
                             focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="">Select churn column...</option>
                  {uploadResult.columns?.map(col => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium
                                  text-gray-700 mb-1">
                  2. What value means churned?
                  <span className="text-red-500"> *</span>
                </label>
                <select
                  value={mapping.churn_yes_value}
                  onChange={(e) => setMapping(p => ({
                    ...p, churn_yes_value: e.target.value
                  }))}
                  disabled={!mapping.churn_col}
                  className="w-full border border-gray-200 rounded-lg
                             px-3 py-2 text-sm focus:outline-none
                             focus:ring-2 focus:ring-blue-500 bg-white
                             disabled:opacity-50"
                >
                  <option value="">Select churned value...</option>
                  {churnColValues.map(val => (
                    <option key={val} value={val}>{val}</option>
                  ))}
                </select>
                {mapping.churn_col && (
                  <p className="text-xs text-gray-400 mt-1">
                    Values: {churnColValues.slice(0, 6).join(", ")}
                  </p>
                )}
              </div>
            </div>

            {/* Auto detect */}
            <div className="p-4 bg-green-50 rounded-lg border border-green-100">
              <p className="text-sm font-medium text-green-700 mb-2">
                Auto-detected by machine:
              </p>
              <div className="grid grid-cols-2 gap-1">
                {[
                  "Tenure / months",    "Monthly charges",
                  "Total charges",      "Contract type",
                  "Internet service",   "Payment method",
                  "Online security",    "Tech support",
                  "Streaming services", "Phone service",
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-1">
                    <CheckCircle size={12}
                      className="text-green-500 shrink-0" />
                    <p className="text-xs text-green-600">{item}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-4 flex items-start gap-2 p-3
                            bg-red-50 rounded-lg border border-red-200">
              <AlertTriangle size={16}
                className="text-red-500 shrink-0 mt-0.5" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="flex gap-3 mt-5">
            <button
              onClick={() => setUploadStep("upload")}
              className="px-4 py-2.5 border border-gray-200
                         text-gray-600 rounded-lg hover:bg-gray-50
                         transition text-sm"
            >
              Back
            </button>
            <button
              onClick={handleStartTraining}
              disabled={!mapping.churn_col || !mapping.churn_yes_value}
              className="flex-1 bg-blue-600 text-white py-2.5
                         rounded-lg hover:bg-blue-700 transition
                         font-medium text-sm flex items-center
                         justify-center gap-2 disabled:opacity-50
                         disabled:cursor-not-allowed"
            >
              <TrendingUp size={16} />
              Auto-Detect and Train Model
            </button>
          </div>
        </div>
      )}

      {/* STEP 3 — TRAINING */}
      {uploadStep === "training" && (
        <div className="bg-white rounded-xl p-6 shadow-sm
                        border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-4">
            Training Progress
          </h3>

          {trainingStatus && (
            <div className="space-y-4">

              {/* Progress bar */}
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600">
                    {trainingStatus.message}
                  </span>
                  <span className="text-sm font-medium text-gray-700">
                    {trainingStatus.progress}%
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div
                    className="h-3 rounded-full transition-all duration-500"
                    style={{
                      width: `${trainingStatus.progress}%`,
                      backgroundColor:
                        trainingStatus.error
                          ? "#ef4444"
                          : trainingStatus.progress === 100
                          ? "#22c55e"
                          : "#3b82f6"
                    }}
                  />
                </div>
              </div>

              {/* Dataset info */}
              {trainingStatus.dataset_info && (
                <div className="p-4 bg-blue-50 rounded-lg
                                border border-blue-100">
                  <p className="text-sm font-medium text-blue-700 mb-3">
                    Dataset Analysis
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-white rounded-lg p-2 text-center">
                      <p className="text-xs text-gray-400">Total Rows</p>
                      <p className="text-lg font-bold text-gray-700">
                        {trainingStatus.dataset_info
                          .total_rows?.toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-2 text-center">
                      <p className="text-xs text-gray-400">Churn Rate</p>
                      <p className="text-lg font-bold text-orange-600">
                        {trainingStatus.dataset_info.churn_rate}
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-2 text-center">
                      <p className="text-xs text-gray-400">Churned</p>
                      <p className="text-lg font-bold text-red-600">
                        {trainingStatus.dataset_info
                          .churned_count?.toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-2 text-center">
                      <p className="text-xs text-gray-400">Retained</p>
                      <p className="text-lg font-bold text-green-600">
                        {trainingStatus.dataset_info
                          .retained_count?.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Steps */}
              {[
                { label: "File uploaded",
                  done: trainingStatus.progress >= 10 },
                { label: "Churn column mapped",
                  done: trainingStatus.progress >= 20 },
                { label: "Columns auto-detected",
                  done: trainingStatus.progress >= 25 },
                { label: "Training Random Forest",
                  done: trainingStatus.progress >= 40 },
                { label: "Building SHAP explainer",
                  done: trainingStatus.progress >= 80 },
                { label: "Model deployed — all pages updated",
                  done: trainingStatus.progress >= 100 },
              ].map((s, i) => (
                <div key={i} className="flex items-center gap-3">
                  {s.done
                    ? <CheckCircle size={16}
                        className="text-green-500 shrink-0" />
                    : trainingStatus.is_training
                    ? <Loader size={16}
                        className="text-blue-500 animate-spin shrink-0" />
                    : <div className="w-4 h-4 rounded-full border-2
                                      border-gray-200 shrink-0" />
                  }
                  <span className={`text-sm ${
                    s.done
                      ? "text-gray-700 font-medium"
                      : "text-gray-400"
                  }`}>
                    {s.label}
                  </span>
                </div>
              ))}

              {/* Error */}
              {trainingStatus.error && (
                <div className="p-4 bg-red-50 rounded-lg
                                border border-red-200">
                  <div className="flex items-start gap-2 mb-2">
                    <AlertTriangle size={16}
                      className="text-red-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-red-700">
                        Training Failed
                      </p>
                      <p className="text-xs text-red-600 mt-1">
                        {trainingStatus.error}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setUploadStep("mapping")}
                    className="mt-2 text-xs text-blue-600 hover:underline"
                  >
                    Go back and fix column selection
                  </button>
                </div>
              )}

              {/* Success */}
              {trainingStatus.last_result && (
                <div className="p-4 bg-green-50 rounded-lg
                                border border-green-200">
                  <div className="flex items-center gap-2 mb-3">
                    <CheckCircle size={16} className="text-green-600" />
                    <p className="text-sm font-medium text-green-700">
                      Training Complete! All pages updated.
                    </p>
                  </div>
                  <p className="text-xs text-green-600 mb-3">
                    Trained on{" "}
                    {trainingStatus.last_result
                      .rows_trained?.toLocaleString()} rows
                    · Churn rate: {trainingStatus.last_result.churn_rate}
                  </p>

                  {Object.entries(trainingStatus.last_result)
                    .filter(([k]) => ![
                      "rows_trained", "churn_rate",
                      "churned_customers", "retained_customers"
                    ].includes(k))
                    .map(([modelName, metrics]) => (
                      <div key={modelName}
                        className="bg-white rounded-lg p-3
                                   border border-green-100 mb-2">
                        <p className="text-xs font-medium
                                      text-gray-700 mb-2">
                          {modelName.replace(/_/g, " ").toUpperCase()}
                        </p>
                        <div className="grid grid-cols-2 gap-2">
                          {Object.entries(metrics).map(([key, val]) => (
                            <div key={key}>
                              <p className="text-xs text-gray-400 capitalize">
                                {key.replace(/_/g, " ")}
                              </p>
                              <p className="text-sm font-medium text-gray-700">
                                {typeof val === "number"
                                  ? (val * 100).toFixed(1) + "%"
                                  : val || "N/A"
                                }
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))
                  }

                  <button
                    onClick={resetUpload}
                    className="w-full mt-3 border border-green-300
                               text-green-700 py-2 rounded-lg
                               hover:bg-green-100 transition text-sm"
                  >
                    Upload Another Dataset
                  </button>
                </div>
              )}

            </div>
          )}
        </div>
      )}

      {/* How it works */}
      <div className="bg-white rounded-xl p-5 shadow-sm
                      border border-gray-100">
        <h3 className="font-semibold text-gray-700 mb-4
                       flex items-center gap-2">
          <TrendingUp size={16} className="text-blue-500" />
          How It Works
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              step:  "1",
              title: "Upload Any CSV",
              desc:  "Any customer dataset — any column names"
            },
            {
              step:  "2",
              title: "Select Churn Column",
              desc:  "Just pick which column and value means churned"
            },
            {
              step:  "3",
              title: "All Pages Update",
              desc:  "Dashboard, Analytics, Retention update automatically"
            },
          ].map((item) => (
            <div key={item.step} className="text-center">
              <div className="w-8 h-8 bg-blue-600 text-white
                              rounded-full flex items-center justify-center
                              text-sm font-bold mx-auto mb-2">
                {item.step}
              </div>
              <p className="text-sm font-medium text-gray-700">
                {item.title}
              </p>
              <p className="text-xs text-gray-400 mt-1">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}