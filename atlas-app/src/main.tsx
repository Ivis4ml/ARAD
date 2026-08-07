import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import { load } from './source'
import './theme.css'

/** 两条数据源：文档里注入的（单文件自包含，不需要服务器）优先，
 *  否则走 /api/runs/...（运行目录，能看历史、能并排比较）。 */
const root = createRoot(document.getElementById('root')!)

function Failed({ message }: { message: string }) {
  return (
    <div className="col" style={{ padding: '60px 0' }}>
      <h1>没有可渲染的投影</h1>
      <p className="muted" style={{ maxWidth: '70ch' }}>
        {message}
      </p>
      <p className="muted small" style={{ marginTop: 12 }}>
        单文件模式：<code>arad atlas render --out &lt;目录&gt;</code>，直接打开生成的
        index.html。运行目录模式：<code>arad atlas serve --runs runs</code>。
      </p>
    </div>
  )
}

load()
  .then((loaded) => {
    root.render(<StrictMode><App loaded={loaded} /></StrictMode>)
  })
  .catch((err: unknown) => {
    root.render(
      <StrictMode>
        <Failed message={err instanceof Error ? err.message : String(err)} />
      </StrictMode>,
    )
  })
