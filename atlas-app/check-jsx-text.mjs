// JSX 里的 **粗体** 不会被渲染，会原样显示给用户。已经漏过三次，改由构建期拦截。
import { readFileSync, readdirSync } from 'node:fs'
const bad = []
for (const f of readdirSync('src').filter((n) => n.endsWith('.tsx'))) {
  readFileSync(`src/${f}`, 'utf8').split('\n').forEach((line, i) => {
    const stripped = line.replace(/^\s*\/[/*].*$/, '').replace(/^\s*\*.*$/, '')
    if (/\*\*[^*\n]+\*\*/.test(stripped)) bad.push(`${f}:${i + 1}: ${line.trim()}`)
  })
}
if (bad.length) {
  console.error('JSX 文本里有未渲染的 markdown 粗体，请改用 <strong>：')
  bad.forEach((b) => console.error('  ' + b))
  process.exit(1)
}
