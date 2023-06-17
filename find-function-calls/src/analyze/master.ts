import { cpus } from 'os';
import { access, mkdir, readdir } from 'fs/promises';
import { resolve } from 'path';
import { isMainThread, Worker } from 'worker_threads';
import { once } from 'events';
import { pathExists } from './util';

async function main() {
  const [datasetDir, outDir, cpuCountStr] = process.argv.slice(2);

  if (!datasetDir) {
    console.error('Usage: node dist/analyze/master.js <dataset-dir> <out-dir>');
    process.exit(1);
  }

  if (!(await pathExists(datasetDir))) {
    console.error(`Dataset directory ${datasetDir} does not exist`);
    process.exit(1);
  }

  await mkdir(outDir, { recursive: true });

  if (!(await pathExists(outDir))) {
    console.error(`Output directory ${outDir} does not exist`);
    process.exit(1);
  }

  const cpuCount = cpuCountStr ? parseInt(cpuCountStr) : cpus().length;
  const tsConfigs = await findTsConfigs(datasetDir);
  // shuffle tsconfigs
  tsConfigs.sort(() => Math.random() - 0.5);

  console.log(`Found ${tsConfigs.length} tsconfigs`);

  const batches: string[][] = [];
  const batchSize = Math.ceil(tsConfigs.length / cpuCount);
  while (tsConfigs.length) {
    batches.push(tsConfigs.splice(0, batchSize));
  }

  const workerExitPromises: Promise<unknown>[] = [];
  for (let i = 0; i < batches.length; i++) {
    const log = (msg: string) => console.log(`[${i}] ${msg}`);

    log('Spawning worker');

    const worker = new Worker(resolve(__dirname, 'worker.js'), {
      workerData: batches[i],
      argv: [datasetDir, outDir],
      resourceLimits: {
        codeRangeSizeMb: 2048,
        stackSizeMb: 2048,
        maxOldGenerationSizeMb: 2048,
        maxYoungGenerationSizeMb: 2048,
      },
    });
    worker.on('message', (message) => {
      log(`Message: ${message}`);
    });

    worker.on('error', (error) => {
      log(`Error: ${error}`);
    });

    worker.on('exit', (code) => {
      log(`Exit: ${code}`);
      worker.removeAllListeners();
    });

    workerExitPromises.push(once(worker, 'exit'));
  }

  await Promise.all(workerExitPromises);
}

async function findTsConfigs(datasetDir: string) {
  const tsConfigPaths: string[] = [];
  datasetDir = resolve(process.cwd(), datasetDir);
  for (const dirent of await readdir(datasetDir, { withFileTypes: true })) {
    if (!dirent.isDirectory()) continue;
    const tsConfigPath = resolve(datasetDir, dirent.name, 'tsconfig.json');
    try {
      await access(tsConfigPath);
      tsConfigPaths.push(tsConfigPath);
    } catch (error) {
      // no tsconfig, bye bye
    }
  }
  return tsConfigPaths;
}

if (isMainThread) {
  main().then(
    () => console.log('Done!'),
    (error) => console.error(error),
  );
}
