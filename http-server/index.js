/**
 * Wumpus world manager and API.
 */
import path from 'node:path';
import http2 from 'node:http2';
import fs from 'node:fs';
import app from './app.js';

const __dirname = path.resolve();
// Browsers dont support HTTP/2 unencrypted even to localhost -- https://http2.github.io/faq/#does-http2-require-encryption.
const cert = fs.readFileSync(__dirname + '/certs/localhost.crt', 'ascii');
const key = fs.readFileSync(__dirname + '/certs/localhost.key', 'ascii');
http2.createSecureServer({
  key,
  cert,
}, app.callback()).listen(3001, () => console.log('Listening 3001'));