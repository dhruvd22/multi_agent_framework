/**
 * WebSocket client for real-time updates.
 */

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(
    private url: string,
    private onMessage: (data: any) => void,
    private onError?: (error: Event) => void
  ) {}

  connect(): void {
    try {
      this.ws = new WebSocket(`${WS_URL}${this.url}`)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.onMessage(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        if (this.onError) {
          this.onError(error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.attemptReconnect()
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.attemptReconnect()
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`)
        this.connect()
      }, this.reconnectDelay * this.reconnectAttempts)
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

export const createExecutionWebSocket = (
  onMessage: (data: any) => void
): WebSocketClient => {
  return new WebSocketClient('/ws/execution', onMessage)
}

export const createLogsWebSocket = (
  onMessage: (data: any) => void
): WebSocketClient => {
  return new WebSocketClient('/ws/logs', onMessage)
}

