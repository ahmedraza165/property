"use client"

import { Card } from "./ui/card"
import { RiskBadge } from "./ui/risk-badge"

interface AIAnalysis {
  imagery: {
    satellite: {
      url: string | null
      source: string | null
    }
    street_view_1: {
      url: string | null
      source: string | null
    }
    street_view_2: {
      url: string | null
      source: string | null
    }
  }
  road_condition: {
    type: string | null
    confidence: number | null
    details?: string | null  // AI-provided remarks
  }
  power_lines: {
    visible: boolean
    confidence: number | null
    distance_meters: number | null
    geometry: string | null
    details?: string | null  // AI-provided description
  }
  power_lines_street?: {
    visible: boolean
    confidence: number | null
    position?: string | null
    proximity?: string | null
    type?: string | null
    details?: string | null  // AI-provided description
  }
  nearby_structures?: {
    structures_detected: boolean
    count: number | null
    types?: string[]
    density?: string | null
    confidence: number | null
    details?: string | null  // AI-provided description
  }
  property_condition?: {
    condition: string | null
    maintained: boolean | null
    development_status?: string | null
    concerns?: string[]
    confidence: number | null
    details?: string | null  // AI-provided description
  }
  nearby_development: {
    type: string | null
    count: number | null
    confidence: number | null
    details?: string | null  // AI-provided description
  }
  overall_risk: {
    level: string | null
    confidence: number | null
    factors?: string[]
    power_lines_detected?: boolean
  }
  key_insights?: string[]  // NEW: 2-3 key insights from AI
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
          <h3 className="text-lg font-semibold">AI Property Analysis</h3>
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

      {/* KEY INSIGHTS - NEW SECTION (Prominent display) */}
      {aiAnalysis.key_insights && aiAnalysis.key_insights.length > 0 && (
        <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl">💡</span>
            <h4 className="text-lg font-bold text-blue-900">Key Property Insights</h4>
          </div>
          <div className="space-y-3">
            {aiAnalysis.key_insights.map((insight, idx) => (
              <div key={idx} className="flex gap-3 items-start bg-white/70 p-4 rounded-lg border border-blue-200">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-bold">
                  {idx + 1}
                </div>
                <p className="text-sm text-gray-800 leading-relaxed flex-1">
                  {insight}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-blue-200">
            <p className="text-xs text-blue-800 italic">
              These insights are generated by analyzing satellite and street view imagery together using advanced AI models.
            </p>
          </div>
        </Card>
      )}

      {/* Imagery Display - NOW SHOWING 3 IMAGES */}
      <Card className="p-6">
        <h4 className="text-md font-semibold mb-4">Property Imagery (3 Angles)</h4>
        <p className="text-xs text-gray-500 mb-4">Multiple angles provide comprehensive AI analysis for better accuracy</p>

        <div className="grid grid-cols-1 gap-4">
          {/* Satellite Image - Top View */}
          <div>
            <p className="text-sm font-medium mb-2 flex items-center gap-2">
              <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded">1</span>
              Satellite View (Top)
            </p>
            {aiAnalysis.imagery.satellite?.url ? (
              <div className="relative">
                <img
                  src={aiAnalysis.imagery.satellite.url}
                  alt="Satellite view from top"
                  className="w-full h-64 object-cover rounded-lg border-2 border-blue-200"
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

          {/* Street View Images - 2 Different Angles */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Street View 1 */}
            <div>
              <p className="text-sm font-medium mb-2 flex items-center gap-2">
                <span className="bg-green-600 text-white text-xs px-2 py-1 rounded">2</span>
                Street View (Angle 1)
              </p>
              {aiAnalysis.imagery.street_view_1?.url ? (
                <div className="relative">
                  <img
                    src={aiAnalysis.imagery.street_view_1.url}
                    alt="Street view angle 1"
                    className="w-full h-64 object-cover rounded-lg border-2 border-green-200"
                  />
                  <span className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                    {aiAnalysis.imagery.street_view_1.source || "Unknown source"}
                  </span>
                </div>
              ) : (
                <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                  <p className="text-gray-400 text-sm">No street view available</p>
                </div>
              )}
            </div>

            {/* Street View 2 */}
            <div>
              <p className="text-sm font-medium mb-2 flex items-center gap-2">
                <span className="bg-purple-600 text-white text-xs px-2 py-1 rounded">3</span>
                Street View (Angle 2)
              </p>
              {aiAnalysis.imagery.street_view_2?.url ? (
                <div className="relative">
                  <img
                    src={aiAnalysis.imagery.street_view_2.url}
                    alt="Street view angle 2"
                    className="w-full h-64 object-cover rounded-lg border-2 border-purple-200"
                  />
                  <span className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                    {aiAnalysis.imagery.street_view_2.source || "Unknown source"}
                  </span>
                </div>
              ) : (
                <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                  <p className="text-gray-400 text-sm">No street view available</p>
                </div>
              )}
            </div>
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

        {/* AI-provided details/remarks */}
        {aiAnalysis.road_condition?.details && (
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-xs font-medium text-blue-900 mb-1">AI Analysis:</p>
            <p className="text-sm text-blue-800 italic">"{aiAnalysis.road_condition.details}"</p>
          </div>
        )}

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
        <h4 className="text-md font-semibold mb-4">Power Infrastructure Analysis</h4>
        <div className="space-y-4">
          {/* Power Line Detection Status */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Electrical Infrastructure:</span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                aiAnalysis.power_lines?.visible || aiAnalysis.power_lines_street?.visible
                  ? "bg-green-100 text-green-800"
                  : "bg-orange-100 text-orange-800"
              }`}
            >
              {aiAnalysis.power_lines?.visible || aiAnalysis.power_lines_street?.visible ? "Yes - Good Access" : "No - May Need Installation"}
            </span>
          </div>

          {/* Street View Power Lines */}
          {aiAnalysis.power_lines_street?.visible && (
            <div className="border-l-4 border-blue-500 pl-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-semibold text-blue-900">📸 Street View Detection</span>
              </div>

              {aiAnalysis.power_lines_street.position && (
                <div className="mb-2">
                  <span className="text-xs font-medium text-gray-600">Position: </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    aiAnalysis.power_lines_street.position === 'directly_above' || aiAnalysis.power_lines_street.position === 'in_front_close' ? 'bg-red-100 text-red-800' :
                    aiAnalysis.power_lines_street.position === 'nearby' ? 'bg-orange-100 text-orange-800' :
                    aiAnalysis.power_lines_street.position === 'far' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {aiAnalysis.power_lines_street.position.replace(/_/g, ' ').toUpperCase()}
                  </span>
                </div>
              )}

              {/* Power Infrastructure Status - INFRASTRUCTURE ACCESS */}
              {aiAnalysis.power_lines_street.position && (
                <div className={`p-3 rounded-lg mb-2 ${
                  aiAnalysis.power_lines_street.position === 'directly_above'
                    ? 'bg-yellow-50 border border-yellow-200'
                    : aiAnalysis.power_lines_street.position === 'in_front_close' || aiAnalysis.power_lines_street.position === 'nearby'
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-blue-50 border border-blue-200'
                }`}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-sm font-bold ${
                      aiAnalysis.power_lines_street.position === 'directly_above'
                        ? 'text-yellow-900'
                        : aiAnalysis.power_lines_street.position === 'in_front_close' || aiAnalysis.power_lines_street.position === 'nearby'
                        ? 'text-green-900'
                        : 'text-blue-900'
                    }`}>
                      {aiAnalysis.power_lines_street.position === 'directly_above' && '⚠️ Electrical Infrastructure - Overhead Clearance Required'}
                      {(aiAnalysis.power_lines_street.position === 'in_front_close' || aiAnalysis.power_lines_street.position === 'nearby') && '✅ Excellent Electrical Infrastructure Access'}
                      {aiAnalysis.power_lines_street.position === 'far' && '✅ Electrical Infrastructure Available in Area'}
                    </span>
                  </div>
                  <p className={`text-xs mb-2 ${
                    aiAnalysis.power_lines_street.position === 'directly_above'
                      ? 'text-yellow-800'
                      : aiAnalysis.power_lines_street.position === 'in_front_close' || aiAnalysis.power_lines_street.position === 'nearby'
                      ? 'text-green-800'
                      : 'text-blue-800'
                  }`}>
                    {aiAnalysis.power_lines_street.position === 'directly_above' &&
                      'Power lines run overhead. Property has electrical infrastructure but requires clearance for tall structures. Easy utility connection available.'}
                    {aiAnalysis.power_lines_street.position === 'in_front_close' &&
                      '✅ POSITIVE: Utility poles nearby provide excellent electrical access. Easy and cost-effective to connect utilities. Good infrastructure for development.'}
                    {aiAnalysis.power_lines_street.position === 'nearby' &&
                      '✅ POSITIVE: Power infrastructure nearby indicates good utility access. No significant installation costs expected. Ideal for residential/commercial development.'}
                    {aiAnalysis.power_lines_street.position === 'far' &&
                      'Electrical infrastructure exists in the area. Utility connection possible with standard extension.'}
                  </p>
                  <div className="bg-white/60 p-2 rounded">
                    <p className={`text-xs ${
                      aiAnalysis.power_lines_street.position === 'directly_above'
                        ? 'text-yellow-900'
                        : aiAnalysis.power_lines_street.position === 'in_front_close' || aiAnalysis.power_lines_street.position === 'nearby'
                        ? 'text-green-900'
                        : 'text-blue-900'
                    }`}>
                      <strong>Position:</strong> {aiAnalysis.power_lines_street.position.replace(/_/g, ' ').toUpperCase()}
                      {aiAnalysis.power_lines_street.type && ` • Type: ${aiAnalysis.power_lines_street.type}`}
                    </p>
                  </div>
                </div>
              )}

              {/* AI Details from Street View */}
              {aiAnalysis.power_lines_street.details && (
                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="text-xs font-medium text-blue-900 mb-1">AI Analysis:</p>
                  <p className="text-xs text-blue-800 italic">"{aiAnalysis.power_lines_street.details}"</p>
                </div>
              )}

              <div className="mt-2 text-xs text-gray-500">
                Confidence: {getConfidenceText(aiAnalysis.power_lines_street.confidence || null)}
                {aiAnalysis.power_lines_street.type && ` • Type: ${aiAnalysis.power_lines_street.type}`}
              </div>
            </div>
          )}

          {/* Satellite Power Lines */}
          {aiAnalysis.power_lines?.visible && (
            <div className="border-l-4 border-purple-500 pl-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-semibold text-purple-900">🛰️ Satellite Detection</span>
              </div>

              {aiAnalysis.power_lines.distance_meters !== null && (
                <div className="mb-2">
                  <span className="text-xs font-medium text-gray-600">Distance from property center: </span>
                  <span className="text-xs font-bold text-purple-900">
                    ~{Math.round(aiAnalysis.power_lines.distance_meters)}m
                  </span>
                </div>
              )}

              {/* AI Details from Satellite */}
              {aiAnalysis.power_lines.details && (
                <div className="bg-purple-50 p-3 rounded-lg mb-2">
                  <p className="text-xs font-medium text-purple-900 mb-1">AI Analysis:</p>
                  <p className="text-xs text-purple-800 italic">"{aiAnalysis.power_lines.details}"</p>
                </div>
              )}

              <div className="text-xs text-gray-500">
                Confidence: {getConfidenceText(aiAnalysis.power_lines.confidence || null)}
              </div>
            </div>
          )}

          {/* No Power Lines - Infrastructure Concern */}
          {!aiAnalysis.power_lines?.visible && !aiAnalysis.power_lines_street?.visible && (
            <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-orange-600 font-bold text-base">⚠️ NO ELECTRICAL INFRASTRUCTURE VISIBLE</span>
              </div>
              <p className="text-sm text-orange-900 font-semibold mb-2">
                No overhead power lines, utility poles, or electrical infrastructure detected in satellite or street view imagery.
              </p>
              <div className="bg-white/50 p-3 rounded-lg mb-2">
                <p className="text-xs text-orange-800">
                  <strong className="text-orange-900">⚠️ INFRASTRUCTURE CONCERN:</strong> Property may lack electrical utility access.
                </p>
                <ul className="list-disc ml-5 mt-2 text-xs text-orange-800 space-y-1">
                  <li>May require expensive electrical utility installation</li>
                  <li>Utility company line extension fees may apply ($5,000-$50,000+)</li>
                  <li>Could need alternative power solutions (solar, generator)</li>
                  <li>Verify electrical service availability with local utility company</li>
                  <li>Higher development costs expected</li>
                </ul>
              </div>
              <p className="text-xs text-orange-900 font-bold">
                ⚠️ Contact local utility company to verify electrical service availability and connection costs before purchase.
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

          {/* AI-provided details */}
          {aiAnalysis.nearby_development?.details && (
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <p className="text-xs font-medium text-purple-900 mb-1">AI Analysis:</p>
              <p className="text-sm text-purple-800 italic">"{aiAnalysis.nearby_development.details}"</p>
            </div>
          )}

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

      {/* Property Condition (if available) */}
      {aiAnalysis.property_condition && (
        <Card className="p-6">
          <h4 className="text-md font-semibold mb-4">Property Condition</h4>
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <span className={`px-4 py-2 rounded-lg font-medium ${
                aiAnalysis.property_condition.condition === 'EXCELLENT' ? 'bg-green-100 text-green-800' :
                aiAnalysis.property_condition.condition === 'GOOD' ? 'bg-blue-100 text-blue-800' :
                aiAnalysis.property_condition.condition === 'AVERAGE' ? 'bg-yellow-100 text-yellow-800' :
                aiAnalysis.property_condition.condition === 'POOR' ? 'bg-orange-100 text-orange-800' :
                aiAnalysis.property_condition.condition === 'VACANT' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {aiAnalysis.property_condition.condition || "Unknown"}
              </span>
              <div className="text-sm text-gray-600">
                Confidence: {getConfidenceText(aiAnalysis.property_condition.confidence || null)}
              </div>
            </div>

            {aiAnalysis.property_condition.details && (
              <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                <p className="text-xs font-medium text-indigo-900 mb-1">AI Analysis:</p>
                <p className="text-sm text-indigo-800 italic">"{aiAnalysis.property_condition.details}"</p>
              </div>
            )}

            {aiAnalysis.property_condition.concerns && aiAnalysis.property_condition.concerns.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-medium text-gray-700 mb-1">Concerns Identified:</p>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {aiAnalysis.property_condition.concerns.map((concern, idx) => (
                    <li key={idx}>{concern}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Nearby Structures (if available) */}
      {aiAnalysis.nearby_structures && aiAnalysis.nearby_structures.structures_detected && (
        <Card className="p-6">
          <h4 className="text-md font-semibold mb-4">Nearby Structures</h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Structures Count:</span>
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {aiAnalysis.nearby_structures.count || 0}
              </span>
            </div>

            {aiAnalysis.nearby_structures.density && (
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Density:</span>
                <span className="text-sm text-gray-600 uppercase">{aiAnalysis.nearby_structures.density}</span>
              </div>
            )}

            {aiAnalysis.nearby_structures.types && aiAnalysis.nearby_structures.types.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-medium text-gray-700 mb-1">Structure Types:</p>
                <div className="flex flex-wrap gap-2">
                  {aiAnalysis.nearby_structures.types.map((type, idx) => (
                    <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                      {type}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {aiAnalysis.nearby_structures.details && (
              <div className="p-4 bg-teal-50 border border-teal-200 rounded-lg">
                <p className="text-xs font-medium text-teal-900 mb-1">AI Analysis:</p>
                <p className="text-sm text-teal-800 italic">"{aiAnalysis.nearby_structures.details}"</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Processing Info */}
      {aiAnalysis.processing_time_seconds !== null && (
        <div className="text-xs text-gray-500 text-center">
          Analysis completed in {aiAnalysis.processing_time_seconds.toFixed(2)} seconds
        </div>
      )}
    </div>
  )
}
