import '@testing-library/jest-dom'

// Polyfill URL.createObjectURL / URL.revokeObjectURL for jsdom
if (!(URL as any).createObjectURL) {
  Object.defineProperty(URL, 'createObjectURL', {
    writable: true,
    value: (() => 'blob:mock') as any,
  })
}
if (!(URL as any).revokeObjectURL) {
  Object.defineProperty(URL, 'revokeObjectURL', {
    writable: true,
    value: (() => {}) as any,
  })
}

// Polyfill Element.scrollTo for jsdom environment used by Vitest
if (!(Element.prototype as any).scrollTo) {
  Object.defineProperty(Element.prototype, 'scrollTo', {
    writable: true,
    value: (() => {}) as any,
  })
}
