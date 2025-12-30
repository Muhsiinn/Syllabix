import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Syllabix</h1>
        </div>
      </header>

      <main className="px-6 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <div className="mb-12">
            <div className="inline-block mb-8">
              <svg
                width="200"
                height="160"
                viewBox="0 0 200 160"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="mx-auto"
              >
                <rect
                  x="20"
                  y="20"
                  width="120"
                  height="160"
                  rx="8"
                  fill="#E8F4FD"
                  transform="rotate(-2 20 20)"
                />
                <rect
                  x="40"
                  y="30"
                  width="120"
                  height="160"
                  rx="8"
                  fill="#D4E9FA"
                  transform="rotate(-1 40 30)"
                />
                <rect
                  x="60"
                  y="40"
                  width="120"
                  height="160"
                  rx="8"
                  fill="#B8DDF7"
                  transform="rotate(0 60 40)"
                />
                <path
                  d="M80 60 L180 60 L180 200 L80 200 Z"
                  fill="#4A90E2"
                  opacity="0.1"
                  rx="8"
                />
                <path
                  d="M100 80 L180 80 L180 200 L100 200 Z"
                  fill="#4A90E2"
                  opacity="0.15"
                  rx="8"
                />
                <circle cx="140" cy="120" r="4" fill="#4A90E2" opacity="0.3" />
                <circle cx="120" cy="140" r="3" fill="#4A90E2" opacity="0.2" />
                <circle cx="160" cy="140" r="3" fill="#4A90E2" opacity="0.2" />
              </svg>
            </div>
          </div>

          <h2 className="text-4xl font-semibold text-gray-900 mb-4">
            Turn past papers into a clear study path.
          </h2>

          <p className="text-lg text-gray-600 mb-12 max-w-2xl mx-auto">
            Upload your past year question papers and let us process them into structured, study-ready materials.
          </p>

          <Link
            href="/upload"
            className="inline-block px-8 py-4 bg-accent text-white rounded-xl font-medium shadow-lg hover:bg-accent-dark transition-colors duration-200"
          >
            Upload past question papers
          </Link>
        </div>
      </main>
    </div>
  )
}

