const path = require("path");
const childProcess = require("child_process");
const vscode = require("vscode");
const {
  LanguageClient,
  TransportKind
} = require("vscode-languageclient/node");

let client;
let debugFactory;
let oplTerminal;

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

  context.subscriptions.push(
    vscode.commands.registerCommand("opl.runCurrentFile", runCurrentFile),
    vscode.commands.registerCommand("opl.debugCurrentFile", debugCurrentFile),
    vscode.commands.registerCommand("opl.runFile", runCurrentFile),
    vscode.commands.registerCommand("opl.debugFile", debugCurrentFile),
    vscode.window.onDidCloseTerminal((terminal) => {
      if (terminal === oplTerminal) {
        oplTerminal = undefined;
      }
    })
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

async function runCurrentFile(resource) {
  const uri = await resolveOplFile(resource);
  if (!uri) {
    return;
  }

  if (!(await ensureOplCli())) {
    return;
  }

  const terminal = getOplTerminal();
  terminal.show(true);
  terminal.sendText(`opl run ${quoteShellPath(uri.fsPath)}`);
}

async function debugCurrentFile(resource) {
  const uri = await resolveOplFile(resource);
  if (!uri) {
    return;
  }

  if (!(await ensureOplCli())) {
    return;
  }

  const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
  const started = await vscode.debug.startDebugging(workspaceFolder, {
    type: "opl",
    request: "launch",
    name: "Debug OPL File",
    program: uri.fsPath
  });

  if (!started) {
    vscode.window.showErrorMessage("Unable to start the OPL debugger.");
  }
}

async function resolveOplFile(resource) {
  const uri = resource && resource.scheme === "file"
    ? resource
    : activeOplEditorUri();

  if (!uri || path.extname(uri.fsPath).toLowerCase() !== ".opl") {
    vscode.window.showErrorMessage("Open an .opl file first.");
    return undefined;
  }

  const editor = vscode.window.activeTextEditor;
  if (editor && editor.document.uri.toString() === uri.toString() && editor.document.isDirty) {
    const saved = await editor.document.save();
    if (!saved) {
      vscode.window.showErrorMessage("Save the current OPL file before running it.");
      return undefined;
    }
  }

  return uri;
}

function activeOplEditorUri() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.isUntitled) {
    return undefined;
  }
  if (editor.document.languageId === "opl" || path.extname(editor.document.fileName).toLowerCase() === ".opl") {
    return editor.document.uri;
  }
  return undefined;
}

function ensureOplCli() {
  return new Promise((resolve) => {
    childProcess.execFile("opl", ["--version"], { windowsHide: true }, (error) => {
      if (error) {
        vscode.window.showErrorMessage("OPL CLI not found. Install with: pip install oplang");
        resolve(false);
        return;
      }
      resolve(true);
    });
  });
}

function getOplTerminal() {
  if (!oplTerminal) {
    oplTerminal = vscode.window.createTerminal({ name: "OPL" });
  }
  return oplTerminal;
}

function quoteShellPath(filePath) {
  return `"${filePath.replace(/"/g, '\\"')}"`;
}

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
