/** 轻量 Markdown 预览渲染（标题 / 列表 / 段落），避免引入 marked。 */

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * 将含 ### 标题的正文转为 HTML。
 * - ### / ## / # → 加粗标题
 * - 有序列表 1. 2.
 * - 无序列表 - / * / - [id]
 */
export function renderSimpleMarkdown(src: string): string {
  if (!src) return ''
  const lines = String(src).replace(/\r\n/g, '\n').split('\n')
  const out: string[] = []
  let inOl = false
  let inUl = false

  const closeLists = () => {
    if (inOl) {
      out.push('</ol>')
      inOl = false
    }
    if (inUl) {
      out.push('</ul>')
      inUl = false
    }
  }

  for (const raw of lines) {
    const line = raw.trimEnd()
    const trimmed = line.trim()

    if (!trimmed) {
      closeLists()
      continue
    }

    const h = trimmed.match(/^(#{1,6})\s+(.+)$/)
    if (h) {
      closeLists()
      const level = Math.min(h[1].length, 3)
      const tag = `h${level}`
      out.push(`<${tag} class="md-h md-h${level}">${escapeHtml(h[2])}</${tag}>`)
      continue
    }

    const ol = trimmed.match(/^(\d+)\.\s+(.+)$/)
    if (ol) {
      if (inUl) {
        out.push('</ul>')
        inUl = false
      }
      if (!inOl) {
        out.push('<ol class="md-ol">')
        inOl = true
      }
      out.push(`<li>${escapeHtml(ol[2])}</li>`)
      continue
    }

    const ul = trimmed.match(/^[-*]\s+(.+)$/)
    if (ul) {
      if (inOl) {
        out.push('</ol>')
        inOl = false
      }
      if (!inUl) {
        out.push('<ul class="md-ul">')
        inUl = true
      }
      // - [1] title: content → 高亮 fact id
      const fact = ul[1].match(/^\[(\d+)\]\s*(.*)$/)
      if (fact) {
        out.push(
          `<li><span class="md-fact">[${escapeHtml(fact[1])}]</span> ${escapeHtml(fact[2])}</li>`,
        )
      } else {
        out.push(`<li>${escapeHtml(ul[1])}</li>`)
      }
      continue
    }

    closeLists()
    out.push(`<p class="md-p">${escapeHtml(trimmed)}</p>`)
  }

  closeLists()
  return out.join('\n')
}
