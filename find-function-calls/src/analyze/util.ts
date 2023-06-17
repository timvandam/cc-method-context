import { access } from 'fs/promises';

export async function pathExists(path: string) {
  try {
    await access(path);
    return true;
  } catch (error) {
    return false;
  }
}