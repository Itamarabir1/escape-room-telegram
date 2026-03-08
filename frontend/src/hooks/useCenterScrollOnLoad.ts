import { useEffect } from 'react'
import type { DependencyList, RefObject } from 'react'

export function useCenterScrollOnLoad(
  ref: RefObject<HTMLDivElement | null>,
  active: boolean,
  deps: DependencyList
): void {
  useEffect(() => {
    if (!active) return
    const run = () => {
      const el = ref.current
      if (!el) return
      const maxScroll = el.scrollWidth - el.clientWidth
      el.scrollLeft = maxScroll > 0 ? maxScroll / 2 : 0
    }
    run()
    requestAnimationFrame(() => requestAnimationFrame(run))
    const t1 = setTimeout(run, 100)
    const t2 = setTimeout(run, 400)
    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
    }
  }, [active, ref, ...deps])
}
