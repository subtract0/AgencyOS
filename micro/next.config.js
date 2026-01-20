/** @type {import('next').NextConfig} */
const path = require('path');

// Load .env from parent AgencyOS directory
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

const nextConfig = {
  reactStrictMode: true,
  env: {
    // Pass through the OpenAI key from parent .env
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
    // Local model configuration
    USE_LOCAL_MODEL: process.env.USE_LOCAL_MODEL || 'false',
    LOCAL_API_BASE: process.env.LOCAL_API_BASE || 'http://localhost:1234/v1',
    LOCAL_MODEL: process.env.LOCAL_MODEL || 'vcoder-120b-1.0-hi-mlx',
  },
}

module.exports = nextConfig
