const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

const devAuthToken = String.fromEnvironment(
  'DEV_AUTH_TOKEN',
  defaultValue: 'prediqo-dev-token',
);
