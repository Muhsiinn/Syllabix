'use client'

interface StepperLayoutProps {
  children: React.ReactNode
  currentStep: number
  totalSteps: number
}

export default function StepperLayout({
  children,
  currentStep,
  totalSteps,
}: StepperLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="px-6 py-4 border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-gray-900">Syllabix</h1>
          <div className="flex items-center space-x-2">
            {Array.from({ length: totalSteps }).map((_, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full transition-colors ${
                  index + 1 === currentStep
                    ? 'bg-accent'
                    : index + 1 < currentStep
                    ? 'bg-green-500'
                    : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>
      </header>

      <main className="px-6 py-12">{children}</main>
    </div>
  )
}

