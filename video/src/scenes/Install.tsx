import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Code, caretBlink, typeLines} from '../components/Code';
import {Scene} from '../components/Scene';
import {SectionHeader} from '../components/SectionHeader';
import {MARGIN, colors, easeInOut, fonts, progress, rise} from '../theme';

// The wheel name and size match `pip wheel .` for this version.
const WHEEL = 'layeris-0.4.0-py3-none-any.whl';
const WHEEL_KB = 19;

const LINES = [
	'$ pip install layeris',
	'Collecting layeris',
	`  Downloading ${WHEEL} (${WHEEL_KB} kB)`,
	'', // the progress bar is drawn over this line
	'Successfully installed layeris-0.4.0',
];
const BAR_LINE = 3;

const FONT_SIZE = 30;
const LINE_HEIGHT = Math.round(FONT_SIZE * 1.7);
const PADDING: [number, number] = [28, 40];
const BAR_WIDTH = 520;
// Sized for the longest line so the block doesn't widen as lines appear.
const BLOCK_WIDTH = Math.ceil(Math.max(...LINES.map((l) => l.length)) * FONT_SIZE * 0.6) + 2 * PADDING[1] + 8;

const BLOCK_IN = 12;
const TYPE_START = BLOCK_IN + 6;
const TYPE_END = TYPE_START + 14;
const COLLECTING_AT = TYPE_END + 4;
const DOWNLOADING_AT = COLLECTING_AT + 5;
const BAR_START = DOWNLOADING_AT + 3;
const BAR_FRAMES = 15;
const DONE_AT = BAR_START + BAR_FRAMES + 4;

export const INSTALL_FRAMES = DONE_AT + 44;

export const Install: React.FC = () => {
	const frame = useCurrentFrame();
	const shown = (at: number) => (frame >= at ? Infinity : 0);
	const reveal = [
		typeLines(LINES[0], frame, [TYPE_START], 1.5)[0],
		shown(COLLECTING_AT),
		shown(DOWNLOADING_AT),
		0,
		shown(DONE_AT),
	];
	const bar = progress(frame, BAR_START, BAR_FRAMES, easeInOut);
	const kb = interpolate(bar, [0, 1], [0, WHEEL_KB]);

	return (
		<Scene>
			<SectionHeader
				index="01"
				title="Install"
				subtitle="Python 3.10 or higher. The only dependencies are NumPy, Pillow and Requests."
			/>
			<div style={{position: 'absolute', left: MARGIN, top: 330, ...rise(frame, BLOCK_IN)}}>
				<div style={{position: 'relative'}}>
					<Code
						code={LINES.join('\n')}
						lang="shell"
						fontSize={FONT_SIZE}
						width={BLOCK_WIDTH}
						padding={PADDING}
						reveal={reveal}
						caret={frame < TYPE_END + 4 ? {line: 0, opacity: caretBlink(frame, TYPE_END)} : undefined}
					/>
					{frame >= BAR_START ? (
						<div
							style={{
								position: 'absolute',
								left: PADDING[1] + FONT_SIZE * 0.6 * 2,
								top: PADDING[0] + BAR_LINE * LINE_HEIGHT,
								height: LINE_HEIGHT,
								display: 'flex',
								alignItems: 'center',
								gap: 22,
								fontFamily: fonts.mono,
								fontSize: FONT_SIZE * 0.85,
								color: colors.muted,
							}}
						>
							<div style={{width: BAR_WIDTH, height: 6, borderRadius: 1, background: colors.rule}}>
								<div style={{width: `${bar * 100}%`, height: '100%', borderRadius: 1, background: colors.string}} />
							</div>
							<span>
								{kb.toFixed(1)}/{WHEEL_KB.toFixed(1)} kB
							</span>
						</div>
					) : null}
				</div>
			</div>
		</Scene>
	);
};
