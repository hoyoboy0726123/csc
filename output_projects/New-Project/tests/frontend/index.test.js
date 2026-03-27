import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import IndexPage from '../../frontend/pages/index'
import * as api from '../../frontend/lib/api'
import * as auth from '../../frontend/lib/auth'
import { useRouter } from 'next/router'

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: jest.fn()
}))

// Mock API calls
jest.mock('../../frontend/lib/api')
jest.mock('../../frontend/lib/auth')

const mockPush = jest.fn()
useRouter.mockReturnValue({ push: mockPush })

describe('IndexPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    auth.getCurrentUser.mockReturnValue({ id: 1, email: 'test@example.com' })
  })

  it('renders the landing page with all main sections', () => {
    render(<IndexPage />)
    expect(screen.getByText(/Voice-to-Code Pipeline/i)).toBeInTheDocument()
    expect(screen.getByText(/從語音構思到可執行代碼/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /開始使用/i })).toBeInTheDocument()
  })

  it('redirects to login when user is not authenticated', async () => {
    auth.getCurrentUser.mockReturnValue(null)
    render(<IndexPage />)
    const startBtn = screen.getByRole('button', { name: /開始使用/i })
    await userEvent.click(startBtn)
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  it('navigates to dashboard when user is authenticated', async () => {
    render(<IndexPage />)
    const startBtn = screen.getByRole('button', { name: /開始使用/i })
    await userEvent.click(startBtn)
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('displays feature cards correctly', () => {
    render(<IndexPage />)
    expect(screen.getByText(/多模態輸入/i)).toBeInTheDocument()
    expect(screen.getByText(/智慧代碼生成/i)).toBeInTheDocument()
    expect(screen.getByText(/雙模態代碼修復/i)).toBeInTheDocument()
  })

  it('shows stats section with animated numbers', () => {
    render(<IndexPage />)
    expect(screen.getByText(/成功生成率 ≥ 70%/i)).toBeInTheDocument()
    expect(screen.getByText(/7 日用戶留存 ≥ 40%/i)).toBeInTheDocument()
    expect(screen.getByText(/端到端耗時 ≤ 15 分鐘/i)).toBeInTheDocument()
  })

  it('renders footer with correct links', () => {
    render(<IndexPage />)
    expect(screen.getByText(/API 文件/i)).toBeInTheDocument()
    expect(screen.getByText(/部署指南/i)).toBeInTheDocument()
    expect(screen.getByText(/GitHub/i)).toBeInTheDocument()
  })

  it('handles keyboard navigation on CTA button', async () => {
    render(<IndexPage />)
    const startBtn = screen.getByRole('button', { name: /開始使用/i })
    startBtn.focus()
    fireEvent.keyDown(startBtn, { key: 'Enter', code: 'Enter' })
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('matches snapshot', () => {
    const { container } = render(<IndexPage />)
    expect(container).toMatchSnapshot()
  })
})