import {
  Project,
  ScriptKind,
  Signature,
  SourceFile,
  ts,
  Node,
  ExportedDeclarations,
} from 'ts-morph';

const DEBUG = false;

export type FileDetails = {
  filePath: string;
  exportedFunctions: FileExportedFunction[];
};

export type FileExportedFunction = {
  signature: string;
  functionCalls: FunctionCall[];
  /**
   * Raw function text
   */
  text: string;
};

export type FunctionCall = {
  /**
   * Name of the function being called
   */
  functionName: string;
  /**
   * Path to the source of this function (can also be a library)
   */
  functionSource: string;
  /**
   * Raw function text
   */
  text: string;
};

export type AnalysisConfig = {
  /**
   * Whether to include type annotations in the found method signatures.
   */
  includeTypeAnnotations: boolean;
};

const defaultConfig: AnalysisConfig = {
  includeTypeAnnotations: false,
};

export function analyzeProjectFiles(
  project: Project,
  config: AnalysisConfig = defaultConfig,
): FileDetails[] {
  const sourceFiles = project.getSourceFiles();

  const fileDetails: FileDetails[] = [];

  for (const sourceFile of sourceFiles) {
    if (sourceFile.getScriptKind() !== ScriptKind.TS) {
      continue;
    }

    const exportedFunctions = findFileExportedFunctions(sourceFile, config);
    fileDetails.push({
      filePath: sourceFile.getFilePath(),
      exportedFunctions,
    });
  }

  return fileDetails;
}

function findFunctionCallsInExportedFunction(
  decl: ExportedDeclarations,
  config: AnalysisConfig = defaultConfig,
): FunctionCall[] {
  if (!Node.isExportGetable(decl) || !decl.isExported()) {
    // make sure it is a top level function that is being called
    throw new Error('Function is not exported');
  }

  const functionSource = decl.getSourceFile().getFilePath();

  const functionCalls: FunctionCall[] = [];

  const functionCallNodes = decl.getDescendantsOfKind(ts.SyntaxKind.CallExpression);
  for (const functionCallNode of functionCallNodes) {
    const functionName = functionCallNode.getFirstChild()?.getText();

    if (!functionName) {
      if (DEBUG) {
        console.warn(
          'Could not find function name for function call node',
          functionCallNode.getText(),
          'in source file',
          decl.getSourceFile().getFilePath(),
        );
      }
      continue;
    }

    const functionNode = functionCallNode.getFirstChild();

    // see if the node being called is a top level exported function
    if (Node.isPropertyAccessExpression(functionNode)) {
      // this is a call on an object member, skip
      continue;
    }

    if (!Node.isIdentifier(functionNode)) {
      // must be an identifier!
      continue;
    }

    functionCalls.push({
      functionName,
      functionSource,
      text: functionCallNode.getText(),
    });
  }

  return functionCalls;
}

function findFileExportedFunctions(
  sourceFile: SourceFile,
  config: AnalysisConfig = defaultConfig,
): FileExportedFunction[] {
  const exportedFunctions: FileExportedFunction[] = [];

  for (const [name, declarations] of sourceFile.getExportedDeclarations()) {
    for (const declaration of declarations) {
      try {
        if (declaration.getFirstAncestorByKind(ts.SyntaxKind.SourceFile) !== sourceFile) {
          continue;
        }

        const declType = declaration.getType();

        // functions
        function handleCallSignature(name: string, sig: Signature) {
          const generics = sig
            .getTypeParameters()
            .map((param) => param.getText())
            .join(', ');
          const returnType = sig
            .getReturnType()
            .getText(declaration)
            .replace(/import\(.+\)\./g, '');

          let signature = `${name}`;
          if (config.includeTypeAnnotations) {
            if (generics) signature += `<${generics}>`;

            const typedParams = sig
              .getParameters()
              .map((param) => {
                const paramName = param.getName();
                const typeStr = param
                  .getTypeAtLocation(declaration)
                  .getText(declaration)
                  .replace(/import\(.+\)\./g, '');
                return `${paramName}: ${typeStr}`;
              })
              .join(', ');
            signature += `(${typedParams}): ${returnType}`;
          } else {
            const params = sig
              .getParameters()
              .map((param) => param.getName())
              .join(', ');

            signature += `(${params})`;
          }

          exportedFunctions.push({
            signature,
            text: declaration.getText(),
            functionCalls: findFunctionCallsInExportedFunction(declaration, config),
          });
        }

        for (const sig of declType.getCallSignatures()) {
          handleCallSignature(name, sig);
        }
      } catch (error) {
        // internal error
      }
    }
  }

  return exportedFunctions;
}
