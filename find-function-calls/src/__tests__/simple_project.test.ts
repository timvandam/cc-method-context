import { analyzeProjectFiles } from '../index';
import { resolve } from 'path';
import { Project } from 'ts-morph';

describe('simple_project', () => {
  const project = new Project({
    tsConfigFilePath: resolve(__dirname, 'test_projects/simple_project/tsconfig.json'),
  });

  it('no types + no objects', () => {
    const projectFileDetails = analyzeProjectFiles(project, {
      includeTypeAnnotations: false,
    });

    expect(projectFileDetails).toHaveLength(2);
    expect(projectFileDetails).toContainEqual({
      exportedFunctions: [
        { signature: 'a(num)', beginCursor: 0, endCursor: 54, functionCalls: [] },
        { signature: 'echo(xyz)', beginCursor: 239, endCursor: 291, functionCalls: [] },
        { signature: 'x()', beginCursor: 305, endCursor: 316, functionCalls: [] },
        { signature: 'y(a)', beginCursor: 331, endCursor: 371, functionCalls: [] },
        { signature: 'z()', beginCursor: 386, endCursor: 397, functionCalls: [] },
        { signature: 'w()', beginCursor: 401, endCursor: 412, functionCalls: [] },
        { signature: 'v()', beginCursor: 416, endCursor: 462, functionCalls: [] },
        { signature: 't()', beginCursor: 478, endCursor: 483, functionCalls: [] },
      ],
      filePath:
        '/home/tim/cc-method-context/find-function-calls/src/__tests__/test_projects/simple_project/src/a.ts',
    });

    expect(projectFileDetails).toContainEqual({
      exportedFunctions: [
        {
          signature: 'b(x)',
          beginCursor: 34,
          endCursor: 102,
          functionCalls: [
            {
              beginCursor: 74,
              endCursor: 78,
              call: 'a(x)',
              functionName: 'a',
              functionSource:
                '/home/tim/cc-method-context/find-function-calls/src/__tests__/test_projects/simple_project/src/b.ts',
            },
            {
              beginCursor: 96,
              endCursor: 99,
              call: 'w()',
              functionName: 'w',
              functionSource:
                '/home/tim/cc-method-context/find-function-calls/src/__tests__/test_projects/simple_project/src/b.ts',
            },
          ],
        },
      ],
      filePath:
        '/home/tim/cc-method-context/find-function-calls/src/__tests__/test_projects/simple_project/src/b.ts',
    });
  });
});
