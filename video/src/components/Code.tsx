import React from 'react';
import {colors, fonts} from '../theme';

export type Lang = 'python' | 'json' | 'shell';

type TokenType =
	| 'plain'
	| 'keyword'
	| 'name'
	| 'call'
	| 'string'
	| 'number'
	| 'comment'
	| 'prompt'
	| 'output';

type Token = {text: string; type: TokenType};

const KEYWORDS = new Set(['from', 'import', 'as', 'for', 'in', 'None', 'True', 'False']);
const NAMES = new Set(['LayerImage', 'np']);

// Matches, in order: strings, comments, numbers, identifiers, anything else.
const TOKEN_RE =
	/("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|(#.*$)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_][A-Za-z0-9_]*)|(\s+|.)/g;

// Same colours and weights as the docs' syntax highlighting.
const STYLES: Record<TokenType, React.CSSProperties> = {
	plain: {color: colors.ink},
	keyword: {color: colors.ink, fontWeight: 500},
	name: {color: colors.ink, fontWeight: 500},
	call: {color: colors.call},
	string: {color: colors.string},
	number: {color: colors.number},
	comment: {color: colors.comment, fontStyle: 'italic'},
	prompt: {color: colors.paren},
	output: {color: colors.muted},
};

export const tokenize = (line: string, lang: Lang): Token[] => {
	if (lang === 'shell') {
		if (line.startsWith('$ ')) {
			return [
				{text: '$ ', type: 'prompt'},
				{text: line.slice(2), type: 'plain'},
			];
		}
		return [{text: line, type: 'output'}];
	}
	const tokens: Token[] = [];
	for (const m of line.matchAll(TOKEN_RE)) {
		const [text, str, comment, num, ident] = m;
		let type: TokenType = 'plain';
		if (str) type = 'string';
		else if (comment) type = 'comment';
		else if (num) type = 'number';
		else if (ident) {
			const rest = line.slice((m.index ?? 0) + text.length);
			if (KEYWORDS.has(ident)) type = 'keyword';
			else if (NAMES.has(ident)) type = 'name';
			else if (rest.startsWith('(')) type = 'call';
		}
		tokens.push({text, type});
	}
	return tokens;
};

/** Keep the first `chars` characters of a token list. */
const slice = (tokens: Token[], chars: number): Token[] => {
	const out: Token[] = [];
	let left = chars;
	for (const t of tokens) {
		if (left <= 0) break;
		out.push(left >= t.text.length ? t : {...t, text: t.text.slice(0, left)});
		left -= t.text.length;
	}
	return out;
};

export type CodeProps = {
	code: string;
	lang?: Lang;
	fontSize?: number;
	lineHeight?: number;
	width?: number;
	padding?: [number, number];
	/** Visible characters per line; lines without an entry are fully visible. */
	reveal?: number[];
	/** Line to draw a text caret on, after its last visible character. */
	caret?: {line: number; opacity: number};
	/** Line to tint, for "this line just ran". */
	highlight?: {line: number; opacity: number};
	style?: React.CSSProperties;
};

export const Code: React.FC<CodeProps> = ({
	code,
	lang = 'python',
	fontSize = 26,
	lineHeight = 1.7,
	width,
	padding = [30, 36],
	reveal,
	caret,
	highlight,
	style,
}) => {
	const lines = code.split('\n');
	const lh = Math.round(fontSize * lineHeight);
	return (
		<div
			style={{
				position: 'relative',
				width,
				padding: `${padding[0]}px ${padding[1]}px`,
				background: colors.code,
				borderRadius: 4,
				fontFamily: fonts.mono,
				fontSize,
				lineHeight: `${lh}px`,
				color: colors.ink,
				whiteSpace: 'pre',
				boxSizing: 'border-box',
				...style,
			}}
		>
			{highlight ? (
				<div
					style={{
						position: 'absolute',
						left: 0,
						right: 0,
						top: padding[0] + highlight.line * lh,
						height: lh,
						background: colors.hover,
						borderLeft: `3px solid ${colors.ink}`,
						opacity: highlight.opacity,
					}}
				/>
			) : null}
			{lines.map((line, i) => {
				const tokens = tokenize(line, lang);
				const visible = reveal?.[i] ?? Infinity;
				const shown = Number.isFinite(visible) ? slice(tokens, visible) : tokens;
				return (
					<div key={i} style={{position: 'relative', height: lh}}>
						{shown.map((t, j) => (
							<span key={j} style={STYLES[t.type]}>
								{t.text}
							</span>
						))}
						{caret && caret.line === i ? (
							<span
								style={{
									display: 'inline-block',
									width: Math.max(2, Math.round(fontSize * 0.08)),
									height: Math.round(fontSize * 1.1),
									marginLeft: 1,
									verticalAlign: 'middle',
									transform: `translateY(-${Math.round(fontSize * 0.06)}px)`,
									background: colors.ink,
									opacity: caret.opacity,
								}}
							/>
						) : null}
					</div>
				);
			})}
		</div>
	);
};

/**
 * Characters to show on each line when typing `code` line by line.
 * `starts[i]` is the frame line i starts typing; lines with no start are
 * shown immediately.
 */
export const typeLines = (
	code: string,
	frame: number,
	starts: (number | undefined)[],
	charsPerFrame = 1.6,
): number[] =>
	code.split('\n').map((line, i) => {
		const start = starts[i];
		if (start === undefined) return line.length;
		return Math.max(0, Math.min(line.length, Math.floor((frame - start) * charsPerFrame)));
	});

/** Blinking caret opacity: solid while typing, then blinks. */
export const caretBlink = (frame: number, typingEnd: number) => {
	if (frame < typingEnd) return 1;
	return Math.floor((frame - typingEnd) / 15) % 2 === 0 ? 1 : 0;
};
