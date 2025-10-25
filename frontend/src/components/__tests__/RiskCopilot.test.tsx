import { render, screen } from '@testing-library/react'
import { RiskCopilot } from '../RiskCopilot'
import { vi } from 'vitest'
import { useRiskStream } from '@/hooks/useRiskStream'

vi.mock('@/hooks/useRiskStream', () => ({
  useRiskStream: vi.fn(),
}))

const mockUseRiskStream = vi.mocked(useRiskStream)

const createMockState = (overrides: Partial<ReturnType<typeof useRiskStream>> = {}) => ({
  score: 0.85,
  connected: true,
  loading: false,
  error: null,
  categories: ['mixer', 'sanctions'],
  reasons: ['Transaction involves known mixer', 'Address on sanctions list'],
  factors: {
    'High volume': 0.78,
    'Cross-chain movement': 0.62,
  },
  start: vi.fn(() => {}),
  stop: vi.fn(() => {}),
  ...overrides,
})

describe('RiskCopilot', () => {
  beforeEach(() => {
    mockUseRiskStream.mockReset()
    mockUseRiskStream.mockReturnValue(createMockState())
  })

  it('renders risk score and categories in full variant', () => {
    render(<RiskCopilot chain="ethereum" address="0x123..." variant="full" />)

    expect(screen.getByText('85')).toBeInTheDocument()
    expect(screen.getByText('mixer')).toBeInTheDocument()
    expect(screen.getByText('sanctions')).toBeInTheDocument()
  })

  it('renders compact variant with limited categories', () => {
    mockUseRiskStream.mockReturnValue(createMockState({
      categories: ['mixer', 'sanctions', 'fraud'],
    }))

    render(<RiskCopilot chain="ethereum" address="0x123..." variant="compact" />)

    expect(screen.getByText('85')).toBeInTheDocument()
    expect(screen.getByText('mixer')).toBeInTheDocument()
    expect(screen.getByText('+1')).toBeInTheDocument()
  })

  it('shows loading state feedback', () => {
    mockUseRiskStream.mockReturnValue(createMockState({
      score: null,
      loading: true,
      connected: false,
      categories: [],
      reasons: [],
      factors: {},
    }))

    render(<RiskCopilot chain="ethereum" address="0x123..." />)

    expect(screen.getByText(/scoring/i)).toBeInTheDocument()
  })

  it('shows error message when hook reports an error', () => {
    mockUseRiskStream.mockReturnValue(createMockState({
      error: 'Network error',
      categories: [],
      reasons: [],
      factors: {},
    }))

    render(<RiskCopilot chain="ethereum" address="0x123..." />)

    expect(screen.getByText('Network error')).toBeInTheDocument()
  })

  it('applies color coding based on score thresholds', () => {
    mockUseRiskStream.mockReturnValue(createMockState({ score: 0.95 }))
    const { container, rerender } = render(<RiskCopilot chain="ethereum" address="0x123..." />)

    let indicator = container.querySelector('div.h-3.w-3.rounded-full') as HTMLElement
    expect(indicator).toHaveClass('bg-red-600')

    mockUseRiskStream.mockReturnValue(createMockState({ score: 0.65 }))
    rerender(<RiskCopilot chain="ethereum" address="0x123..." />)
    indicator = container.querySelector('div.h-3.w-3.rounded-full') as HTMLElement
    expect(indicator).toHaveClass('bg-orange-500')

    mockUseRiskStream.mockReturnValue(createMockState({ score: 0.35 }))
    rerender(<RiskCopilot chain="ethereum" address="0x123..." />)
    indicator = container.querySelector('div.h-3.w-3.rounded-full') as HTMLElement
    expect(indicator).toHaveClass('bg-emerald-500')
  })
})
