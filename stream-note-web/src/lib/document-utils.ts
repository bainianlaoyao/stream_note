import type { DocumentContent } from '@/types/document'

export function extractTextBlocks(content: DocumentContent): string[] {
  const blocks: string[] = []

  function traverse(node: any) {
    if (node && typeof node === 'object') {
      if (node.type === 'paragraph') {
        const nodeContent = node.content || []
        if (Array.isArray(nodeContent)) {
          const paragraph = nodeContent
            .filter((c: any) => typeof c === 'object' && c.text)
            .map((c: any) => c.text)
            .join('')
            .trim()
          if (paragraph) {
            blocks.push(paragraph)
          }
        } else if (typeof nodeContent === 'string') {
          const paragraph = nodeContent.trim()
          if (paragraph) {
            blocks.push(paragraph)
          }
        }
      }
      if (node.content) {
        traverse(node.content)
      }
    } else if (Array.isArray(node)) {
      for (const item of node) {
        traverse(item)
      }
    }
  }

  if (content && content.content) {
    traverse(content.content)
  }
  return blocks
}

export function getTaskContext(content: DocumentContent | null, taskText: string): { before: string | null, after: string | null } {
  if (!content) return { before: null, after: null }
  
  const blocks = extractTextBlocks(content)
  const index = blocks.findIndex(b => b.includes(taskText))
  
  if (index === -1) return { before: null, after: null }
  
  return {
    before: index > 0 ? blocks[index - 1] : null,
    after: index < blocks.length - 1 ? blocks[index + 1] : null
  }
}
