// frontend/src/services/api.js

import axios from "axios"

const BASE_URL = import.meta.env.VITE_API_URL?.replace('/api/v1', '') || "http://localhost:8000"

const API = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
API.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || "Something went wrong"
    console.log("Full error:", error.response?.status, error.response?.data)

    if (error.response?.status === 401) {
      localStorage.removeItem("token")
      localStorage.removeItem("user")
      window.location.href = "/login"
    }

    return Promise.reject(new Error(message))
  }
)

// -----------------------------------------------
// AUTH
// -----------------------------------------------
export const registerUser = (data) => API.post("/auth/register", data)
export const loginUser    = (data) => API.post("/auth/login",    data)
export const getMe        = ()     => API.get("/auth/me")

// -----------------------------------------------
// PREDICTION
// -----------------------------------------------
export const predictChurn = (data) => API.post("/predict", data)

// -----------------------------------------------
// ANALYTICS
// -----------------------------------------------
export const getAnalytics      = ()  => API.get("/analytics/summary")
export const getModelFeatures  = ()  => API.get("/analytics/model-features")
export const getDatasetColumns = ()  => API.get("/analytics/dataset-columns")

// -----------------------------------------------
// CUSTOMERS
// -----------------------------------------------
export const getCustomers = (page = 1, limit = 10) =>
  API.get(`/customers?page=${page}&limit=${limit}`)

export const getAllPredictions = (page = 1, limit = 10, risk = null, search = null) => {
  let url = `/customers/predictions?page=${page}&limit=${limit}`
  if (risk && risk !== "All") url += `&risk=${risk}`
  if (search) url += `&search=${search}`
  return API.get(url)
}

export const getCustomerPredictions = (customerId) =>
  API.get(`/customers/predictions/${customerId}`)

export const getPredictionStats = () =>
  API.get("/customers/stats")

export const deletePrediction = (id) =>
  API.delete(`/customers/predictions/${id}`)

// -----------------------------------------------
// REPORTS
// -----------------------------------------------
export const downloadAnalyticsReport = async () => {
  const response = await fetch(
    `${BASE_URL}/api/v1/reports/analytics`,
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    }
  )
  if (!response.ok) throw new Error("Failed to generate report")
  const blob = await response.blob()
  const url  = window.URL.createObjectURL(blob)
  const a    = document.createElement("a")
  a.href     = url
  a.download = "ChurnAI_Analytics_Report.pdf"
  a.click()
  window.URL.revokeObjectURL(url)
}

export const downloadCustomerReport = async (predictionData) => {
  const response = await fetch(
    `${BASE_URL}/api/v1/reports/customer`,
    {
      method:  "POST",
      headers: {
        "Content-Type":  "application/json",
        "Authorization": `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify(predictionData),
    }
  )
  if (!response.ok) throw new Error("Failed to generate report")
  const blob = await response.blob()
  const url  = window.URL.createObjectURL(blob)
  const a    = document.createElement("a")
  a.href     = url
  a.download = `ChurnAI_Customer_${predictionData.customer_id}.pdf`
  a.click()
  window.URL.revokeObjectURL(url)
}

export default API