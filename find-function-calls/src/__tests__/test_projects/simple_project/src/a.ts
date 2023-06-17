export function a(num: number) {
  return 123 + num;
}
export const obj = {
  x(num: number) {
    return num - 1;
  },
  y: (str: string) => str + '!',
  z: function h<T>(a: T) {
    return a;
  },
  w<T>(b: T): T {
    return b;
  },
};
export function echo<T>(xyz: T): T {
  return xyz;
}
export const x = () => 1;
export const y = function (a: string) {
  return 2;
};
export const z = () => 3,
  w = () => 4,
  v = function asd() {
    return 'hee hee';
  };

export const t = x;

export * from './b';
