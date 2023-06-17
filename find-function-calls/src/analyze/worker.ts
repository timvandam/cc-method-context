import { isMainThread, workerData, threadId } from 'worker_threads';
import { analyzeProjectFiles } from '../index';
import { Project } from 'ts-morph';
import { resolve, dirname } from 'path';
import { writeFile } from 'fs/promises';
import { pathExists } from './util';

async function main() {
  const [datasetDir, outDir] = process.argv.slice(2);
  const tsConfigPaths = workerData;
  assertWorkerData(tsConfigPaths);

  for (const tsConfigPath of tsConfigPaths) {
    // await writeFile(`tsconfig-${threadId}`, tsConfigPath + '\n', 'utf-8');
    try {
      await analyzeTsConfig(tsConfigPath, outDir);
    } catch (error) {
      console.error(`Error analyzing ${tsConfigPath}: ${error}`);
    }
  }
}

function assertWorkerData(data: unknown): asserts data is string[] {
  if (!Array.isArray(data)) {
    throw new Error('Expected workerData to be an array');
  }

  for (const item of data) {
    if (typeof item !== 'string') {
      throw new Error('Expected workerData to be an array of strings');
    }
  }
}

async function analyzeTsConfig(tsConfigFilePath: string, outDir: string) {
  const outPath = resolve(outDir, `${dirname(tsConfigFilePath).split('/').pop()!}.json`);

  if (await pathExists(outPath)) {
    return;
  }

  const project = new Project({ tsConfigFilePath });
  const fileDetails = analyzeProjectFiles(project);
  await writeFile(outPath, JSON.stringify(fileDetails), 'utf-8');
}

if (!isMainThread) {
  main().then(
    () => console.log('Done!'),
    (error) => console.error(error),
  );
}
