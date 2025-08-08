// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import { spawn } from 'child_process';
import path = require('path');
import * as vscode from 'vscode';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated

	let provider = vscode.languages.registerCompletionItemProvider(
		{ scheme: 'file', language: 'markdown' },
		new AutoCompleterProvider(),
		''
	)

	context.subscriptions.push(provider);

    // provider = vscode.languages.registerCompletionItemProvider(
	// 	{ scheme: 'file', language: 'jinja-md' },
	// 	new AutoCompleterProvider(),
	// 	''
	// )

	// context.subscriptions.push(provider);
}

// This method is called when your extension is deactivated
export function deactivate() {}

type KWRange = {
    toComplete?: string,
    replaceRange: vscode.Range
};

type ItemInfo = {
    path: string,
    cat: string,
    rel?: string
}

type InputPair = [string, ItemInfo]

class AutoCompleterProvider implements vscode.CompletionItemProvider {
	
    keywordAndRangeFromWordrange(document: vscode.TextDocument, position: vscode.Position): KWRange {
		let wordRange = document.getWordRangeAtPosition(position);
		if (!wordRange) return { toComplete: undefined, replaceRange: new vscode.Range(position, position)};

        const line = document.lineAt(position.line);

        let left = wordRange.start.character - 1;
        while (left >= 0 && line.text.charAt(left) != '[') {
            left -= 1
        }
        const overwriteBefore = wordRange.start.character - left;
        let right = wordRange.end.character;
        let overwriteAfter = line.text.charAt(right) == ']' ? 1 : 0

        const replaceRange = wordRange.with(
            wordRange.start.translate(0, -overwriteBefore), 
            wordRange.end.translate(0, overwriteAfter)
        );
        
        const toComplete = document.getText(replaceRange).replace(/\[|\]/g, '');
        console.log("karfwt", { toComplete, replaceRange })
        return { toComplete, replaceRange }
    }

	async provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): Promise<vscode.CompletionItem[]> {
        
        const { toComplete, replaceRange } = this.keywordAndRangeFromWordrange(document, position);
        if (!toComplete)
            return []

        const suggestions = await this.getSuggestions(toComplete, document);
        // Convert to VS Code completion items
        return suggestions.map(suggestion => {
            const [text, info] = suggestion;
            const item = new vscode.CompletionItem(text, vscode.CompletionItemKind.Text);	
            item.insertText = this.formatLink(text, info).slice(1);
			item.range = new vscode.Range(replaceRange.start.translate(0, 1), replaceRange.end);
            // You can customize these properties based on your needs:
            item.detail = this.formatDetail(text, info);
            // item.documentation = 'More detailed info';
            // item.insertText = suggestion; // What gets inserted
            console.dir(item)
            return item;
        });
    }

    private formatDetail(text: string, info: ItemInfo): string {
        const cat = {
            "v": "Venue",
            "tt": "Team/Faction",
            "o": "Organization",
            "w": "Talent",
            "a": "Talent alias",
            "c": "Championship"
        }[info.cat] || '??'

        if (info.rel)
            return `${cat} (${info.rel})`
        else
            return cat
    }

    private formatLink(text: string, info: ItemInfo): string {
        return `[${text}](${info.path})`
    }

    private async getSuggestions(
        input: string, 
        document: vscode.TextDocument, 
    ): Promise<InputPair[]> {
        return new Promise((resolve, reject) => {
            // Get the path to your autocompleter tool from settings
            const config = vscode.workspace.getConfiguration('autocompleter');
            const toolPath = config.get<string>('toolPath', 'your-autocompleter-tool');
            const timeout = config.get<number>('timeout', 1000);
			const workspaceFolder = vscode.workspace.workspaceFolders?.[0]!;
            const workspaceRoot = workspaceFolder?.uri.fsPath;
            
            // Spawn your command-line tool
            const process = spawn(path.join(workspaceRoot, toolPath), ["--json"], {
                stdio: ['pipe', 'pipe', 'pipe'],
				cwd: workspaceRoot
            });

            let output = '';
            let errorOutput = '';
            let timeoutId: NodeJS.Timeout;

            // Set up timeout
            timeoutId = setTimeout(() => {
                process.kill();
                resolve([]);
            }, timeout);

            // Collect stdout
            process.stdout.on('data', (data) => {
                output += data.toString();
            });

            // Collect stderr for debugging
            process.stderr.on('data', (data) => {
                errorOutput += data.toString();
            });

            // Handle process completion
            process.on('close', (code) => {
                clearTimeout(timeoutId);
                if (code === 0) {
                    const suggestions = JSON.parse(output)
                    resolve(suggestions);
                } else {
                    console.error(`Autocompleter tool failed with code ${code}: ${errorOutput}`);
                    resolve([]); // Return empty array on error
                }
            });

            // Handle process errors
            process.on('error', (error) => {
                clearTimeout(timeoutId);
                console.error(`Failed to start autocompleter tool: ${error.message}`);
                resolve([]);
            });

            // Send input to the tool's stdin
            process.stdin.write(input);
            process.stdin.end();
        });
    }
}