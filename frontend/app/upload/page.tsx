'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import UploadZone from '@/components/UploadZone'
import FileList from '@/components/FileList'
import StepperLayout from '@/components/StepperLayout'

interface FileWithInfo {
  file: File
  id: string
  pageCount?: number
}

export default function UploadPage() {
  const [files, setFiles] = useState<FileWithInfo[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const router = useRouter()

  const handleFilesAdded = (newFiles: File[]) => {
    const filesWithInfo: FileWithInfo[] = newFiles.map((file) => ({
      file,
      id: Math.random().toString(36).substring(7),
    }))
    setFiles((prev) => [...prev, ...filesWithInfo])
  }

  const handleRemoveFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  const handleStartProcessing = async () => {
    if (files.length === 0) return

    setIsProcessing(true)

    try {
      const formData = new FormData()
      files.forEach((fileWithInfo) => {
        formData.append('files', fileWithInfo.file)
      })

      const response = await fetch('http://localhost:8000/upload-files', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Upload failed')
      }

      const data = await response.json()
      router.push(`/processing/${data.job_id}`)
    } catch (error) {
      console.error('Upload error:', error)
      alert(error instanceof Error ? error.message : 'Upload failed')
      setIsProcessing(false)
    }
  }

  return (
    <StepperLayout currentStep={1} totalSteps={2}>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-semibold text-gray-900 mb-2">
            Upload past year question papers
          </h1>
          <p className="text-gray-600">
            Upload one or more question paper PDFs. We'll process them step by step.
          </p>
        </div>

        <div className="mb-6">
          <UploadZone onFilesAdded={handleFilesAdded} />
        </div>

        {files.length > 0 && (
          <div className="mb-8">
            <FileList files={files} onRemove={handleRemoveFile} />
          </div>
        )}

        <div className="flex justify-center">
          <button
            onClick={handleStartProcessing}
            disabled={files.length === 0 || isProcessing}
            className="px-8 py-4 bg-accent text-white rounded-xl font-medium shadow-lg hover:bg-accent-dark transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isProcessing ? 'Processing...' : 'Start processing'}
          </button>
        </div>
      </div>
    </StepperLayout>
  )
}

