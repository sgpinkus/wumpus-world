module.exports = {
  parser: '@typescript-eslint/parser',
  plugins: ['solid'],
  extends: ['eslint:recommended', 'plugin:solid/typescript'],
  env: {
    node: true,
    mocha: true,
    es2021: true,
  },
  parserOptions: {
    sourceType: 'module',
    ecmaVersion: 'latest',
    requireConfigFile: false,
  },
  rules: {
    'no-var': 'warn',
    'eqeqeq': 'warn',
    'keyword-spacing': 'error',
    'handle-callback-err': 'error',
    'no-console': 0,
    'linebreak-style': 0,
    'react/no-unescaped-entities': 0,
    'quotes': [ 'error', 'single', { avoidEscape: true, allowTemplateLiterals: true } ],
    'semi': ['error', 'always'],
    'semi-spacing': 'error',
    'spaced-comment': 0,
    'vue/multi-word-component-names': 'off',
    'comma-dangle': ['warn', 'always-multiline'],
    'no-unused-vars': [
      'warn',
      { vars: 'all', args: 'all', argsIgnorePattern: '^_|this', ignoreRestSiblings: false },
    ],
  },
};

