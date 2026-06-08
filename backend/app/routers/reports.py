// Report endpoints
export const downloadAnalyticsReport = async () => {
  const response = await fetch(
    "http://localhost:8000/api/v1/reports/analytics",
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
    "http://localhost:8000/api/v1/reports/customer",
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