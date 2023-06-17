import { a, obj, w } from './a';

export function b(x: number) {
  return a(x) * 2 + obj.x(x) + w();
}
