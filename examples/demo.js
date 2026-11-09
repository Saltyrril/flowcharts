function find(arr, x) {
  for (let i = 0; i < arr.length; i++) {
    if (arr[i] === x) return i;
  }
  return -1;
}
const sq = (a) => {
  return a * a;
};
let r = find([1,2,3], 2);
console.log(r)
while (r > 0) { r-- }
