/** 显示格式。**只改显示位数，不改数值**；原值放 title 属性。 */

export function num(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  return value.toFixed(digits)
}

export function int(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  return String(value)
}

export function short(hash: string | null | undefined, n = 12): string {
  return hash ? hash.slice(0, n) : '—'
}

export function when(iso: string | null | undefined): string {
  if (!iso) return '—'
  return iso.replace('T', ' ').replace(/\.\d+/, '').replace(/[+]\d{2}:\d{2}$/, '')
}

export const METRIC_LABELS: Record<string, string> = {
  abs_t: '|t| 统计量',
  ic_spearman: 'IC（时序 Spearman）',
  sharpe: 'Sharpe（pre-cost）',
}

/** 哪些指标配零假设带。
 *  |t| 用「n 次独立检验下 |z| 最大值的期望」（双侧，搜索接受任一方向）；
 *  Sharpe 用「n 次试验下 Sharpe 最大值的期望」（单侧，搜索只挑最大的），
 *  尺度取自本链自身的 Sharpe 离散度，因此至少要两次有定义的试验。
 *  IC 没有配：它的零假设离散度不能用同一套办法从本链估出来。 */
export const METRIC_HAS_NULL_BAND: Record<string, boolean> = {
  abs_t: true,
  ic_spearman: false,
  sharpe: true,
}
