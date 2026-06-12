import {
  createContext, useContext, useState,
  useEffect, useCallback, useRef
} from "react"
import API from "../services/api"

const DataContext = createContext(null)

export function DataProvider({ children }) {
  // Analytics data
  const [summary,     setSummary]     = useState(null)
  const [datasetInfo, setDatasetInfo] = useState(null)
  const [loading,     setLoading]     = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  // Upload state — persists across page navigation
  const [uploadStep,      setUploadStep]      = useState("upload")
  const [uploadResult,    setUploadResult]    = useState(null)
  const [trainingStatus,  setTrainingStatus]  = useState(null)
  const [uploadedFile,    setUploadedFile]    = useState(null)
  const [isPolling,       setIsPolling]       = useState(false)

  const pollRef = useRef(null)

  // Fetch analytics data
  const fetchAllData = useCallback(async () => {
    setLoading(true)
    try {
      const [summaryData, datasetData] = await Promise.all([
        API.get("/analytics/summary"),
        API.get("/upload/dataset/info"),
      ])
      setSummary(summaryData)
      setDatasetInfo(datasetData)
      setLastUpdated(new Date())
      console.log("✅ Data refreshed:", summaryData)
    } catch (err) {
      console.error("Error fetching data:", err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAllData()
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [fetchAllData])

  const refreshData = useCallback(async () => {
    console.log("🔄 Refreshing all data...")
    await fetchAllData()
  }, [fetchAllData])

  // Start polling training status
  const startPolling = useCallback(() => {
    setIsPolling(true)
    if (pollRef.current) clearInterval(pollRef.current)

    pollRef.current = setInterval(async () => {
      try {
        const status = await API.get("/upload/status")
        setTrainingStatus(status)

        if (!status.is_training) {
          clearInterval(pollRef.current)
          setIsPolling(false)

          if (status.progress === 100) {
            // Training complete — refresh all pages
            console.log("✅ Training complete — refreshing all data")
            await fetchAllData()
          }
        }
      } catch (err) {
        clearInterval(pollRef.current)
        setIsPolling(false)
      }
    }, 2000)
  }, [fetchAllData])

  // Reset upload state
  const resetUpload = useCallback(() => {
    setUploadStep("upload")
    setUploadResult(null)
    setTrainingStatus(null)
    setUploadedFile(null)
    if (pollRef.current) clearInterval(pollRef.current)
    setIsPolling(false)
  }, [])

  return (
    <DataContext.Provider value={{
      // Analytics
      summary,
      datasetInfo,
      loading,
      lastUpdated,
      refreshData,

      // Upload state
      uploadStep,      setUploadStep,
      uploadResult,    setUploadResult,
      trainingStatus,  setTrainingStatus,
      uploadedFile,    setUploadedFile,
      isPolling,
      startPolling,
      resetUpload,
    }}>
      {children}
    </DataContext.Provider>
  )
}

export function useData() {
  const context = useContext(DataContext)
  if (!context) {
    throw new Error("useData must be used inside DataProvider")
  }
  return context
}