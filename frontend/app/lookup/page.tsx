"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Search, FileText, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function LookupPage() {
  const router = useRouter()
  const [jobId, setJobId] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!jobId.trim()) {
      setError('Please enter a Job ID')
      return
    }

    // Validate UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    if (!uuidRegex.test(jobId.trim())) {
      setError('Invalid Job ID format. Please check and try again.')
      return
    }

    setIsLoading(true)

    try {
      // Check if job exists
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/status/${jobId.trim()}`)

      if (response.ok) {
        const data = await response.json()

        // Redirect based on status
        if (data.status === 'completed') {
          router.push(`/results/${jobId.trim()}`)
        } else if (data.status === 'processing') {
          router.push(`/status/${jobId.trim()}`)
        } else if (data.status === 'failed') {
          setError(`Job failed: ${data.error_message || 'Unknown error'}`)
          setIsLoading(false)
        } else {
          router.push(`/status/${jobId.trim()}`)
        }
      } else if (response.status === 404) {
        setError('Job ID not found. Please check your Job ID and try again.')
        setIsLoading(false)
      } else {
        setError('Unable to retrieve job. Please try again later.')
        setIsLoading(false)
      }
    } catch (error) {
      setError('Connection error. Please check your internet and try again.')
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-2xl mx-auto"
        >
          {/* Header */}
          <div className="text-center mb-12">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
              className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-blue-100 mb-6"
            >
              <Search className="w-10 h-10 text-blue-600" />
            </motion.div>
            <h1 className="text-4xl font-bold text-slate-900 mb-4">
              Find Your Results
            </h1>
            <p className="text-lg text-slate-600">
              Access your property analysis from any device
            </p>
          </div>

          {/* Lookup Form */}
          <Card className="p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="jobId" className="block text-sm font-medium text-slate-700 mb-2">
                  Job ID
                </label>
                <input
                  type="text"
                  id="jobId"
                  value={jobId}
                  onChange={(e) => {
                    setJobId(e.target.value)
                    setError('')
                  }}
                  placeholder="e.g., 550e8400-e29b-41d4-a716-446655440000"
                  className="w-full px-4 py-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  disabled={isLoading}
                />
                <p className="mt-2 text-sm text-slate-500">
                  Enter the Job ID you received after uploading your CSV
                </p>
              </div>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg"
                >
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-800">{error}</p>
                </motion.div>
              )}

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Looking up...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5 mr-2" />
                    Find My Results
                  </>
                )}
              </Button>
            </form>
          </Card>

          {/* Info Cards */}
          <div className="grid md:grid-cols-2 gap-6 mt-8">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Card className="p-6">
                <FileText className="w-8 h-8 text-blue-600 mb-4" />
                <h3 className="font-semibold text-slate-900 mb-2">
                  Where to find your Job ID?
                </h3>
                <p className="text-sm text-slate-600">
                  Your Job ID is displayed after uploading a CSV file. Save it to access your results from any device.
                </p>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card className="p-6">
                <Search className="w-8 h-8 text-green-600 mb-4" />
                <h3 className="font-semibold text-slate-900 mb-2">
                  Access Anywhere
                </h3>
                <p className="text-sm text-slate-600">
                  Your results are stored securely in the database. Access them from any browser or device.
                </p>
              </Card>
            </motion.div>
          </div>

          {/* Back Link */}
          <div className="text-center mt-8">
            <button
              onClick={() => router.push('/')}
              className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              ← Back to Home
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
