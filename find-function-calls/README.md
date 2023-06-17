# find-function-calls

Scripts that use the TypeScript compiler API to find where methods/functions are being called.
These are the points at which we will perform code completion to investigate whether correct/available methods are being used

# analyze
```bash
tsc -b
node ./dist/analyze/master.js
```