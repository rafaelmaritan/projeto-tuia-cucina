import { cp, mkdir, rm, writeFile } from 'node:fs/promises';
import { dirname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const deploymentDirectory = dirname(fileURLToPath(import.meta.url));
const projectDirectory = resolve(deploymentDirectory, '..');
const sourceDirectory = resolve(projectDirectory, 'frontend');
const outputDirectory = resolve(deploymentDirectory, 'dist');
const configuredApiUrl = process.env.PUBLIC_API_BASE_URL?.trim();

if (!configuredApiUrl) {
  throw new Error('Set PUBLIC_API_BASE_URL to the HTTPS origin of the deployed API.');
}

let apiUrl;
try {
  apiUrl = new URL(configuredApiUrl);
} catch {
  throw new Error('PUBLIC_API_BASE_URL must be a valid absolute URL.');
}

if (
  apiUrl.protocol !== 'https:'
  || apiUrl.username
  || apiUrl.password
  || apiUrl.pathname !== '/'
  || apiUrl.search
  || apiUrl.hash
) {
  throw new Error('PUBLIC_API_BASE_URL must be an HTTPS origin without credentials, path, query, or fragment.');
}

const deploymentRoot = resolve(deploymentDirectory);
if (!outputDirectory.startsWith(`${deploymentRoot}${sep}`)) {
  throw new Error('Refusing to write outside the deployment output directory.');
}

await rm(outputDirectory, { recursive: true, force: true });
await mkdir(outputDirectory, { recursive: true });
await cp(sourceDirectory, outputDirectory, {
  recursive: true,
  filter: (sourcePath) => sourcePath !== resolve(sourceDirectory, 'config.js'),
});
await writeFile(
  resolve(outputDirectory, 'config.js'),
  `window.tuiaConfig = ${JSON.stringify({ apiBaseUrl: `${apiUrl.origin}/api` }, null, 2)};\n`,
  'utf8',
);

console.log(`Cloudflare Pages output generated at ${outputDirectory}`);
