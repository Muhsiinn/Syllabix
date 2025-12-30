'use client'

import { useEffect, useState } from 'react'

interface ProgressStepProps {
  title: string
  status: 'pending' | 'active' | 'completed'
  detail?: string
  progress?: number
  currentPage?: number
  totalPages?: number
  currentFile?: string | null
}

export default function ProgressStep({
  title,
  status,
  detail,
  progress,
  currentPage,
  totalPages,
  currentFile,
}: ProgressStepProps) {
  const [animatedProgress, setAnimatedProgress] = useState(0)
  const [pageCounter, setPageCounter] = useState(0)

  useEffect(() => {
    if (progress !== undefined && status === 'active') {
      const targetProgress = Math.min(100, Math.max(0, progress))
      const duration = 300
      const startProgress = animatedProgress
      const startTime = Date.now()

      let animationFrameId: number

      const animate = () => {
        const elapsed = Date.now() - startTime
        const progressRatio = Math.min(1, elapsed / duration)
        const easeOutCubic = 1 - Math.pow(1 - progressRatio, 3)
        const currentProgress = startProgress + (targetProgress - startProgress) * easeOutCubic

        setAnimatedProgress(currentProgress)

        if (progressRatio < 1) {
          animationFrameId = requestAnimationFrame(animate)
        } else {
          setAnimatedProgress(targetProgress)
        }
      }

      animationFrameId = requestAnimationFrame(animate)

      return () => {
        if (animationFrameId) {
          cancelAnimationFrame(animationFrameId)
        }
      }
    }
  }, [progress, status])

  useEffect(() => {
    if (currentPage !== undefined && currentPage > 0) {
      setPageCounter(currentPage)
    }
  }, [currentPage])

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-start">
        <div className="flex-shrink-0 mr-4">
          {status === 'completed' ? (
            <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center transition-all duration-300">
              <svg
                className="w-5 h-5 text-green-600"
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
          ) : status === 'active' ? (
            <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center">
              <div className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
              <div className="w-4 h-4 rounded-full bg-gray-300" />
            </div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h3
            className={`text-base font-medium mb-1 transition-colors duration-200 ${
              status === 'completed'
                ? 'text-green-700'
                : status === 'active'
                ? 'text-accent'
                : 'text-gray-500'
            }`}
          >
            {title}
          </h3>
          {detail && (
            <p className="text-sm text-gray-600 mb-2">{detail}</p>
          )}
          {currentFile && status === 'active' && (
            <p className="text-xs text-gray-500 mb-2 truncate">
              Current: {currentFile}
            </p>
          )}
          {progress !== undefined && status === 'active' && (
            <div className="mt-3 space-y-2">
              <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-accent to-accent-light h-2.5 rounded-full transition-all duration-300 ease-out relative"
                  style={{ width: `${animatedProgress}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse" />
                </div>
              </div>
              {totalPages && totalPages > 0 && (
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span className="font-medium text-accent">
                    Page {pageCounter} of {totalPages}
                  </span>
                  <span className="font-medium">
                    {Math.round(animatedProgress)}%
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

