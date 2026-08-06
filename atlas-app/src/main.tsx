import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import type { Projection } from './types'
import './theme.css'

/** 数据由 Python 渲染器注入 <head> 的 script 标签，页面因此不发任何网络请求。 */
function readProjection(): Projection | null {
  const node = document.getElementById('atlas-data')
  if (!node || !node.textContent) return null
  try {
    return JSON.parse(node.textContent) as Projection
  } catch {
    return null
  }
}

const projection = readProjection()
const root = createRoot(document.getElementById('root')!)
root.render(
  <StrictMode>
    {projection ? (
      <App p={projection} />
    ) : (
      <div className="col" style={{ padding: '60px 0' }}>
        <h1>没有可渲染的投影</h1>
        <p className="muted">
          本页需要由 <code>arad atlas render</code> 注入账本投影。
          直接打开构建产物只会看到这一页 —— 这是刻意的：Atlas 不自带任何数据。
        </p>
      </div>
    )}
  </StrictMode>,
)
