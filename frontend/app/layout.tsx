import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Syllabix - Turn past papers into a clear study path',
  description: 'Upload and process past year question papers to create structured study materials',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

