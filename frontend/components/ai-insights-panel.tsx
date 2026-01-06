"use client"

import { Card } from "./ui/card"
import { RiskBadge } from "./ui/risk-badge"

interface AIAnalysis {
  imagery: {
    satellite: {
      url: string | null
      source: string | null
    }
    street: {
      url: string | null
      source: string | null
    }
  }
  road_condition: {
    type: string | null
    confidence: number | null
  }
  power_lines: {
    visible: boolean
    confidence: number | null
    distance_meters: number | null
    geometry: string | null
  }
  nearby_development: {
    type: string | null
    count: number | null
    confidence: number | null
  }
  overall_risk: {
    level: string | null
    confidence: number | null
  }
  processing_time_seconds: number | null
  model_version: string | null
  analyzed_at: string | null
  error: string | null
}

interface AIInsightsPanelProps {
  aiAnalysis: AIAnalysis | null
  propertyAddress: string
}

export function AIInsightsPanel({ aiAnalysis, propertyAddress }: AIInsightsPanelProps) {
  if (!aiAnalysis) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">AI Analysis</h3>
        <p className="text-gray-500 text-sm">
          No AI analysis available for this property yet. Trigger AI analysis from the main results page.
        </p>
      </Card>
    )
  }

  if (aiAnalysis.error) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">AI Analysis</h3>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm">
            Error: {aiAnalysis.error}
          </p>
        </div>
      </Card>
    )
  }

  const getRoadConditionColor = (type: string | null) => {
    if (!type) return "gray"
    switch (type.toUpperCase()) {
      case "PAVED":
        return "green"
      case "GRAVEL":
        return "yellow"
      case "DIRT":
        return "orange"
      case "POOR":
        return "red"
      default:
        return "gray"
    }
  }

  const getConfidenceText = (confidence: number | null) => {
    if (confidence === null) return "Unknown"
    const percentage = Math.round(confidence * 100)
    if (percentage >= 80) return `${percentage}% (High)`
    if (percentage >= 50) return `${percentage}% (Medium)`
    return `${percentage}% (Low)`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">AI-Powered Property Analysis</h3>
          {aiAnalysis.overall_risk?.level && (
            <RiskBadge risk={aiAnalysis.overall_risk.level.toLowerCase()} />
          )}
        </div>
        <p className="text-sm text-gray-600 mb-2">{propertyAddress}</p>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>Model: {aiAnalysis.model_version || "v1.0"}</span>
          <span>•</span>
          <span>Confidence: {getConfidenceText(aiAnalysis.overall_risk?.confidence || null)}</span>
          {aiAnalysis.analyzed_at && (
            <>
              <span>•</span>
              <span>Analyzed: {new Date(aiAnalysis.analyzed_at).toLocaleDateString()}</span>
            </>
          )}
        </div>
      </Card>

      {/* Imagery Display */}
      <Card className="p-6">
        <h4 className="text-md font-semibold mb-4">Property Imagery</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Satellite Image */}
          <div>
            <p className="text-sm font-medium mb-2">Satellite View</p>
            {aiAnalysis.imagery.satellite?.url ? (
              <div className="relative">
                <img
                  src={aiAnalysis.imagery.satellite.url}
                  alt="Satellite view"
                  className="w-full h-64 object-cover rounded-lg border border-gray-200"
                />
                <span className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                  {aiAnalysis.imagery.satellite.source || "Unknown source"}
                </span>
              </div>
            ) : (
              <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                <p className="text-gray-400 text-sm">No satellite imagery available</p>
              </div>
            )}
          </div>

          {/* Street View Image */}
          <div>
            <p className="text-sm font-medium mb-2">Street View</p>
            {aiAnalysis.imagery.street?.url ? (
              <div className="relative">
                <img
                  src={aiAnalysis.imagery.street.url}
                  alt="Street view"
                  className="w-full h-64 object-cover rounded-lg border border-gray-200"
                />
                <span className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                  {aiAnalysis.imagery.street.source || "Unknown source"}
                </span>
              </div>
            ) : (
              <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                <p className="text-gray-400 text-sm">No street view available</p>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Road Condition */}
      <Card className="p-6">
        <h4 className="text-md font-semibold mb-4">Road Condition Analysis</h4>
        <div className="flex items-center gap-4 mb-4">
          <div
            className={`px-4 py-2 rounded-lg font-medium bg-${getRoadConditionColor(
              aiAnalysis.road_condition?.type
            )}-100 text-${getRoadConditionColor(aiAnalysis.road_condition?.type)}-800`}
          >
            {aiAnalysis.road_condition?.type || "Unknown"}
          </div>
          <div className="text-sm text-gray-600">
            Confidence: {getConfidenceText(aiAnalysis.road_condition?.confidence || null)}
          </div>
        </div>
        <div className="text-sm text-gray-600">
          {aiAnalysis.road_condition?.type === "PAVED" && (
            <p>Property has paved road access, which is ideal for development and accessibility.</p>
          )}
          {aiAnalysis.road_condition?.type === "DIRT" && (
            <p>
              Property has unpaved dirt road access. This may affect development costs and
              accessibility, especially during wet weather.
            </p>
          )}
          {aiAnalysis.road_condition?.type === "GRAVEL" && (
            <p>
              Property has gravel road access. This provides reasonable accessibility but may
              require periodic maintenance.
            </p>
          )}
          {aiAnalysis.road_condition?.type === "POOR" && (
            <p>
              Road condition is poor with significant damage. Road improvements may be needed for
              development.
            </p>
          )}
        </div>
      </Card>

      {/* Power Lines Detection */}
      <Card className="p-6">
        <h4 className="text-md font-semibold mb-4">Power Infrastructure</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Power Lines Detected:</span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                aiAnalysis.power_lines?.visible
                  ? "bg-yellow-100 text-yellow-800"
                  : "bg-green-100 text-green-800"
              }`}
            >
              {aiAnalysis.power_lines?.visible ? "Yes" : "No"}
            </span>
          </div>

          {aiAnalysis.power_lines?.visible && (
            <>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Confidence:</span>
                <span className="text-sm text-gray-600">
                  {getConfidenceText(aiAnalysis.power_lines?.confidence || null)}
                </span>
              </div>

              {aiAnalysis.power_lines?.distance_meters !== null && (
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Estimated Distance:</span>
                  <span className="text-sm text-gray-600">
                    ~{Math.round(aiAnalysis.power_lines.distance_meters)} meters
                  </span>
                </div>
              )}

              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  Power lines detected near the property. This may provide electricity access but
                  could also affect property aesthetics and require easement considerations.
                </p>
              </div>
            </>
          )}

          {!aiAnalysis.power_lines?.visible && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                No visible power lines detected in the immediate vicinity. Verify electricity
                availability through utility providers.
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Nearby Development */}
      <Card className="p-6">
        <h4 className="text-md font-semibold mb-4">Surrounding Development</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Development Type:</span>
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              {aiAnalysis.nearby_development?.type || "Unknown"}
            </span>
          </div>

          {aiAnalysis.nearby_development?.count !== null && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Structures Detected:</span>
              <span className="text-sm text-gray-600">{aiAnalysis.nearby_development.count}</span>
            </div>
          )}

          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Confidence:</span>
            <span className="text-sm text-gray-600">
              {getConfidenceText(aiAnalysis.nearby_development?.confidence || null)}
            </span>
          </div>

          <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
            <p className="text-sm text-gray-700">
              {aiAnalysis.nearby_development?.type === "RESIDENTIAL" &&
                "Area shows residential development patterns."}
              {aiAnalysis.nearby_development?.type === "COMMERCIAL" &&
                "Area has commercial development characteristics."}
              {aiAnalysis.nearby_development?.type === "INDUSTRIAL" &&
                "Area shows industrial development patterns."}
              {aiAnalysis.nearby_development?.type === "AGRICULTURAL" &&
                "Area appears to be primarily agricultural."}
              {aiAnalysis.nearby_development?.type === "UNDEVELOPED" &&
                "Area appears largely undeveloped or rural."}
              {aiAnalysis.nearby_development?.type === "UNKNOWN" &&
                "Development pattern could not be determined from available imagery."}
            </p>
          </div>
        </div>
      </Card>

      {/* Processing Info */}
      {aiAnalysis.processing_time_seconds !== null && (
        <div className="text-xs text-gray-500 text-center">
          Analysis completed in {aiAnalysis.processing_time_seconds.toFixed(2)} seconds
        </div>
      )}
    </div>
  )
}
