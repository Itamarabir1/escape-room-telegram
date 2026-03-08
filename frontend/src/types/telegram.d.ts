declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        version?: string
        ready?: () => void | Promise<void>
        expand?: () => void
        initData?: string
        initDataUnsafe?: { user?: { first_name?: string }; start_param?: string }
        sendData?: (data: string) => void
        BackButton?: {
          show: () => void
          hide: () => void
          onClick: (callback: () => void) => void
          offClick: (callback: () => void) => void
        }
        onEvent?: (eventType: string, callback: () => void) => void
        offEvent?: (eventType: string, callback: () => void) => void
      }
    }
  }
}

export {}
