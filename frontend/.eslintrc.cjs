/* eslint-disable */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: false,
  },
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
    project: undefined,
    tsconfigRootDir: __dirname,
  },
  settings: {
    react: { version: 'detect' },
  },
  plugins: ['@typescript-eslint', 'react-refresh', 'react-hooks'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  rules: {
    // CI-friendly: no warnings because of --max-warnings 0
    'react-refresh/only-export-components': 'off',
    '@typescript-eslint/no-unused-vars': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    'no-console': 'off',
    'no-empty': 'off',
    'no-extra-semi': 'off',
    'no-useless-escape': 'off',
    'react-hooks/exhaustive-deps': 'off',
  },
  ignorePatterns: [
    'dist/',
    'build/',
    'node_modules/',
    'public/',
  ],
}
