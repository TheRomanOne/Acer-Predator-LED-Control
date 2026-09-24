import { act, renderHook } from '@testing-library/react'
import { StrictMode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useDebouncedEffect } from './hooks'

describe('useDebouncedEffect', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('does not fire for the initial value, even under StrictMode double effects', () => {
    const effect = vi.fn()

    renderHook(() => useDebouncedEffect({ n: 1 }, 50, effect), { wrapper: StrictMode })
    act(() => vi.advanceTimersByTime(200))

    expect(effect).not.toHaveBeenCalled()
  })

  it('fires once with the latest value after the value settles', () => {
    const effect = vi.fn()
    const { rerender } = renderHook(
      ({ value }: { value: number }) => useDebouncedEffect(value, 50, effect),
      { initialProps: { value: 1 } },
    )

    rerender({ value: 2 })
    act(() => vi.advanceTimersByTime(20))
    rerender({ value: 3 })
    act(() => vi.advanceTimersByTime(60))

    expect(effect).toHaveBeenCalledTimes(1)
    expect(effect).toHaveBeenCalledWith(3)
  })
})
