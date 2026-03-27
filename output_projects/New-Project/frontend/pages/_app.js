import '../styles/globals.css'
import { useEffect } from 'react'
import { useRouter } from 'next/router'
import { AuthProvider } from '../lib/auth'

function MyApp({ Component, pageProps }) {
  const router = useRouter()

  useEffect(() => {
    // 全局錯誤處理
    const handleError = (event) => {
      console.error('Global error:', event.error)
    }
    window.addEventListener('error', handleError)
    return () => window.removeEventListener('error', handleError)
  }, [])

  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  )
}

export default MyApp