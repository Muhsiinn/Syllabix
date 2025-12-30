'use client'

import { useEffect, useState, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import ProgressStep from '@/components/ProgressStep'
import StepperLayout from '@/components/StepperLayout'

interface StreamUpdate {
  type: string
  stage?: string
  processed_pages?: number
  total_pages?: number
  current_page?: number
  current_file?: string
  processed_files?: number
  total_files?: number
  error?: string
}

interface ProcessingState {
  stage: string
  total_files: number
  processed_files: number
  total_pages: number
  processed_pages: number
  current_file: string | null
  current_page: number
  error: string | null
}

export default function ProcessingPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.jobId as string
  const [state, setState] = useState<ProcessingState>({
    stage: 'pending',
    total_files: 0,
    processed_files: 0,
    total_pages: 0,
    processed_pages: 0,
    current_file: null,
    current_page: 0,
    error: null,
  })
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!jobId) return

    const eventSource = new EventSource(
      `http://localhost:8000/processing-stream/${jobId}`
    )

    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const update: StreamUpdate = JSON.parse(event.data)

        if (update.type === 'initial_status') {
          setState((prev) => ({
            ...prev,
            stage: update.stage || prev.stage,
            total_files: update.total_files || prev.total_files,
            processed_files: update.processed_files || prev.processed_files,
            total_pages: update.total_pages || prev.total_pages,
            processed_pages: update.processed_pages || prev.processed_pages,
            current_file: update.current_file || null,
            current_page: update.processed_pages || prev.current_page,
          }))
        } else if (update.type === 'stage_change') {
          setState((prev) => ({
            ...prev,
            stage: update.stage || prev.stage,
            total_pages: update.total_pages !== undefined ? update.total_pages : prev.total_pages,
            total_files: update.total_files !== undefined ? update.total_files : prev.total_files,
          }))
        } else if (update.type === 'file_change') {
          setState((prev) => ({
            ...prev,
            current_file: update.current_file || null,
            processed_files: update.processed_files !== undefined ? update.processed_files : prev.processed_files,
            total_files: update.total_files !== undefined ? update.total_files : prev.total_files,
          }))
        } else if (update.type === 'page_progress') {
          setState((prev) => ({
            ...prev,
            processed_pages: update.processed_pages !== undefined ? update.processed_pages : prev.processed_pages,
            total_pages: update.total_pages !== undefined ? update.total_pages : prev.total_pages,
            current_page: update.current_page !== undefined ? update.current_page : prev.current_page,
            current_file: update.current_file || prev.current_file,
          }))
        } else if (update.type === 'error') {
          setState((prev) => ({
            ...prev,
            error: update.error || 'An error occurred',
            stage: 'failed',
          }))
          eventSource.close()
        }

        if (update.stage === 'completed') {
          setTimeout(() => {
            eventSource.close()
          }, 500)
        }
      } catch (error) {
        console.error('Error parsing stream update:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error)
      eventSource.close()
    }

    return () => {
      eventSource.close()
    }
  }, [jobId])

  const getStageStatus = (stage: string) => {
    const stages = ['reading_files', 'extracting_pages', 'structuring']
    const currentIndex = stages.indexOf(state.stage)
    const targetIndex = stages.indexOf(stage)

    if (targetIndex < currentIndex) return 'completed'
    if (targetIndex === currentIndex) return 'active'
    return 'pending'
  }

  return (
    <StepperLayout currentStep={2} totalSteps={2}>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-semibold text-gray-900 mb-2">
            Processing question papers
          </h1>
          <p className="text-gray-600">
            This may take a few moments. You can stay on this page.
          </p>
        </div>

        <div className="space-y-4 mb-8">
          <ProgressStep
            title="Reading PDF files"
            status={getStageStatus('reading_files')}
            detail={
              state.total_files > 0
                ? `${state.total_files} file${state.total_files !== 1 ? 's' : ''} detected`
                : 'Detecting files...'
            }
          />

          <ProgressStep
            title="Extracting pages"
            status={getStageStatus('extracting_pages')}
            detail={
              state.total_pages > 0
                ? `Processing page ${state.current_page} of ${state.total_pages}`
                : 'Preparing pages...'
            }
            progress={
              state.total_pages > 0
                ? (state.processed_pages / state.total_pages) * 100
                : 0
            }
            currentPage={state.current_page}
            totalPages={state.total_pages}
            currentFile={state.current_file}
          />

          <ProgressStep
            title="Structuring questions"
            status={getStageStatus('structuring')}
            detail="Organizing content..."
          />
        </div>

        {state.error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-800">
            <p className="font-medium">Error:</p>
            <p>{state.error}</p>
          </div>
        )}

        {state.stage === 'completed' && (
          <div className="text-center">
            <div className="mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <svg
                  className="w-8 h-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <p className="text-lg font-medium text-gray-900">
                Processing completed successfully
              </p>
            </div>
            <button
              onClick={() => router.push('/')}
              className="px-8 py-4 bg-accent text-white rounded-xl font-medium shadow-lg hover:bg-accent-dark transition-colors duration-200"
            >
              Continue
            </button>
          </div>
        )}
      </div>
    </StepperLayout>
  )
}

