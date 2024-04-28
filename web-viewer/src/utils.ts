export function range(max) {
  return Array.from(Array(max)).map((_v,i) => i);
}

export function cellIndex(x: number, y: number, n: number) {
  if (x < 0 || x >= n) throw new Error(`X must be between [0,${n}] (${x})`);
  if (y < 0 || y >= n) throw new Error(`Y must be between [0,${n}] (${y})`);
  return x + y*n;
}