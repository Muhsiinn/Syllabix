'use client'

interface FileWithInfo {
  file: File
  id: string
  pageCount?: number
}

interface FileListProps {
  files: FileWithInfo[]
  onRemove: (id: string) => void
}

export default function FileList({ files, onRemove }: FileListProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Uploaded Files ({files.length})
      </h3>
      <div className="space-y-3">
        {files.map((fileWithInfo) => (
          <div
            key={fileWithInfo.id}
            className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center flex-1 min-w-0">
              <div className="flex-shrink-0 mr-4">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="text-red-500"
                >
                  <path
                    d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <polyline
                    points="14 2 14 8 20 8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {fileWithInfo.file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(fileWithInfo.file.size)}
                  {fileWithInfo.pageCount !== undefined &&
                    ` • ${fileWithInfo.pageCount} page${
                      fileWithInfo.pageCount !== 1 ? 's' : ''
                    }`}
                </p>
              </div>
            </div>
            <button
              onClick={() => onRemove(fileWithInfo.id)}
              className="ml-4 p-2 text-gray-400 hover:text-red-500 transition-colors"
              aria-label="Remove file"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

