const path = require("path");
const vscode = require("vscode");
const {
  LanguageClient,
  TransportKind
} = require("vscode-languageclient/node");

let client;
let debugFactory;

function activate(context) {
  const workspaceRoot = path.dirname(context.extensionPath);
  const python = process.env.OPL_PYTHON || "python";
  const pythonPath = [
    workspaceRoot,
    process.env.PYTHONPATH
  ].filter(Boolean).join(path.delimiter);
  const lspArgs = process.env.OPL_LSP_PATH
    ? [process.env.OPL_LSP_PATH]
    : ["-m", "opl_lsp.server"];

  const serverOptions = {
    command: python,
    args: lspArgs,
    transport: TransportKind.stdio,
    options: {
      cwd: workspaceRoot,
      env: {
        ...process.env,
        PYTHONPATH: pythonPath
      }
    }
  };

  const clientOptions = {
    documentSelector: [{ scheme: "file", language: "opl" }],
    synchronize: {
      fileEvents: vscode.workspace.createFileSystemWatcher("**/*.opl")
    }
  };

  client = new LanguageClient(
    "opl-lsp",
    "OPL Language Server",
    serverOptions,
    clientOptions
  );

  context.subscriptions.push(client);
  client.start();

  debugFactory = new OPLDebugAdapterFactory(workspaceRoot, python, pythonPath);
  context.subscriptions.push(
    vscode.debug.registerDebugAdapterDescriptorFactory("opl", debugFactory)
  );
}

function deactivate() {
  if (!client) {
    return undefined;
  }
  return client.stop();
}

module.exports = {
  activate,
  deactivate
};

class OPLDebugAdapterFactory {
  constructor(workspaceRoot, python, pythonPath) {
    this.workspaceRoot = workspaceRoot;
    this.python = python;
    this.pythonPath = pythonPath;
  }

  createDebugAdapterDescriptor() {
    const dapArgs = process.env.OPL_DAP_PATH
      ? [process.env.OPL_DAP_PATH]
      : ["-m", "opl_dap.server"];

    return new vscode.DebugAdapterExecutable(
      this.python,
      dapArgs,
      {
        cwd: this.workspaceRoot,
        env: {
          ...process.env,
          PYTHONPATH: this.pythonPath
        }
      }
    );
  }
}
