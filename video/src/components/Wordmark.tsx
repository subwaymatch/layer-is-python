import React from 'react';
import {colors, fonts} from '../theme';

export const WORD = 'layeris';
export const FRAMES_PER_CHAR = 2;

/**
 * The lowercase DM Mono wordmark from the docs home page, typed one letter at
 * a time. Every letter is laid out from the start so the word never shifts.
 */
export const Wordmark: React.FC<{
	fontSize: number;
	frame: number;
	start: number;
	/** Frames the caret keeps blinking after the last letter. */
	caretHold?: number;
}> = ({fontSize, frame, start, caretHold = 20}) => {
	const typed = Math.max(0, Math.min(WORD.length, Math.floor((frame - start) / FRAMES_PER_CHAR) + 1));
	const typingEnd = start + WORD.length * FRAMES_PER_CHAR;
	const caretVisible =
		frame >= start - 6 &&
		frame < typingEnd + caretHold &&
		(frame < typingEnd || Math.floor((frame - typingEnd) / 10) % 2 === 0);
	return (
		<div
			style={{
				position: 'relative',
				fontFamily: fonts.mono,
				fontWeight: 400,
				fontSize,
				lineHeight: 1.05,
				letterSpacing: '-0.03em',
				color: colors.ink,
				whiteSpace: 'pre',
			}}
		>
			{WORD.split('').map((ch, i) => (
				<span key={i} style={{opacity: frame >= start && i < typed ? 1 : 0, position: 'relative'}}>
					{ch}
					{caretVisible && i === (frame < start ? -1 : typed - 1) ? <Caret fontSize={fontSize} /> : null}
				</span>
			))}
			{caretVisible && frame < start ? (
				<span style={{position: 'absolute', left: 0, top: 0, bottom: 0}}>
					<Caret fontSize={fontSize} />
				</span>
			) : null}
		</div>
	);
};

const Caret: React.FC<{fontSize: number}> = ({fontSize}) => (
	<span
		style={{
			position: 'absolute',
			left: '100%',
			top: '50%',
			marginLeft: fontSize * 0.04,
			width: Math.max(2, fontSize * 0.045),
			height: fontSize * 0.92,
			transform: 'translateY(-50%)',
			background: colors.ink,
			opacity: 1,
		}}
	/>
);
