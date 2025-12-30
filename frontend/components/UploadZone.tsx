'use client'

import { useCallback, useState } from 'react'

interface UploadZoneProps {
  onFilesAdded: (files: File[]) => void
}

export default function UploadZone({ onFilesAdded }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)

      const files = Array.from(e.dataTransfer.files).filter(
        (file) => file.type === 'application/pdf'
      )

      if (files.length > 0) {
        onFilesAdded(files)
      }
    },
    [onFilesAdded]
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []).filter(
        (file) => file.type === 'application/pdf'
      )

      if (files.length > 0) {
        onFilesAdded(files)
      }

      e.target.value = ''
    },
    [onFilesAdded]
  )

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`
        border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200
        ${
          isDragging
            ? 'border-accent bg-accent/5'
            : 'border-gray-300 bg-white hover:border-gray-400'
        }
      `}
    >
      <input
        type="file"
        id="file-upload"
        multiple
        accept=".pdf"
        onChange={handleFileInput}
        className="hidden"
      />
      <label
        htmlFor="file-upload"
        className="cursor-pointer flex flex-col items-center"
      >
        <div className="mb-4">
          <svg
            width="64"
            height="64"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            className="text-gray-400 mx-auto"
          >
            <path
              d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <polyline
              points="17 8 12 3 7 8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <line
              x1="12"
              y1="3"
              x2="12"
              y2="15"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <p className="text-lg font-medium text-gray-700 mb-2">
          Drag and drop PDF files here
        </p>
        <p className="text-sm text-gray-500 mb-4">or</p>
        <span className="inline-block px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
          Browse files
        </span>
        <p className="text-xs text-gray-400 mt-4">PDF files only</p>
      </label>
    </div>
  )
}

