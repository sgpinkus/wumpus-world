module.exports = {
  env: {
    es6: true,
    node: true,
    mocha: true,
  },
  extends: ['eslint:recommended'],
  parserOptions: {
    sourceType: 'module',
    ecmaVersion: 'latest',
    requireConfigFile: false,
  },
  plugins: ['mocha'],
  rules: {
    'indent': ['error', 2],
    'quotes': ['error', 'single'],
    'linebreak-style': ['error', 'unix'],
    'semi': ['error', 'always'],
    // 'no-console': ['error', { allow: ['warn', 'error', 'debug'] }],
    'no-unused-vars': [
      'warn',
      { vars: 'all', args: 'all', argsIgnorePattern: '^_', ignoreRestSiblings: false },
    ],
  },
  ignorePatterns: [
    'build/',
    'node_modules/',
  ],
};
