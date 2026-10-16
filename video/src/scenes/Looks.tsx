import React from 'react';
import {Sequence, useCurrentFrame} from 'remotion';
import {Code} from '../components/Code';
import {Wipe} from '../components/Photo';
import {Scene} from '../components/Scene';
import {SectionHeader} from '../components/SectionHeader';
import assets from '../data/assets.json';
import {MARGIN, colors, easeInOut, fonts, progress, rise} from '../theme';

const {looks} = assets;

type LookData = (typeof looks)[number];

const FIRST_DELAY = 20;
const WIPE_FRAMES = 42;
const HOLD_FRAMES = 56;
const LOOK_EXIT = 14;

const IMAGE_W = 840;
const IMAGE_H = 560;
const TOP = 318;

const pythonCode = (look: LookData) =>
	`image = LayerImage.from_file("${look.photo}")\n${look.code}`;

/** When each part of a look appears, in frames from the look's start. */
const timing = (look: LookData) => {
	const codeStart = 12;
	const presetLines = look.preset ? look.preset.split('\n').length : 0;
	const pythonStart = codeStart + (look.preset ? presetLines * 3 + 8 : 0);
	const wipeStart = pythonStart + pythonCode(look).split('\n').length * 5 + 16;
	const duration = wipeStart + WIPE_FRAMES + HOLD_FRAMES + LOOK_EXIT;
	return {codeStart, pythonStart, wipeStart, duration};
};

const STARTS = looks.reduce<number[]>(
	(acc, _look, i) => [...acc, i === 0 ? FIRST_DELAY : acc[i - 1] + timing(looks[i - 1]).duration],
	[],
);

export const LOOKS_FRAMES = STARTS[looks.length - 1] + timing(looks[looks.length - 1]).duration;

/** Lines appear one after another rather than being typed. */
const lineReveal = (code: string, frame: number, start: number, every = 5) =>
	code.split('\n').map((_, i) => (frame >= start + i * every ? Infinity : 0));

const Look: React.FC<{look: LookData; last: boolean}> = ({look, last}) => {
	const frame = useCurrentFrame();
	const {codeStart, pythonStart, wipeStart, duration} = timing(look);
	const exit = last ? 0 : progress(frame, duration - LOOK_EXIT, LOOK_EXIT, easeInOut);
	const python = pythonCode(look);
	const presetName = `${look.slug}.json`;
	const t = progress(frame, wipeStart, WIPE_FRAMES, easeInOut);

	return (
		<div style={{position: 'absolute', inset: 0, opacity: 1 - exit}}>
			<div style={{position: 'absolute', left: MARGIN, top: TOP, width: 770}}>
				<h3
					style={{
						margin: '0 0 22px',
						fontFamily: fonts.sans,
						fontWeight: 600,
						fontSize: 34,
						color: colors.ink,
						...rise(frame, 4),
					}}
				>
					{look.title}
				</h3>
				{look.preset ? (
					<div style={{marginBottom: 22, ...rise(frame, codeStart - 4)}}>
						<div style={{fontFamily: fonts.mono, fontSize: 19, color: colors.muted, marginBottom: 10}}>
							{presetName}
						</div>
						<Code
							code={look.preset}
							lang="json"
							fontSize={17}
							lineHeight={1.75}
							padding={[18, 22]}
							reveal={lineReveal(look.preset, frame, codeStart, 3)}
						/>
					</div>
				) : null}
				<div style={rise(frame, pythonStart - 4)}>
					<Code
						code={python}
						fontSize={look.preset ? 20 : 22}
						padding={look.preset ? [18, 22] : [26, 30]}
						reveal={lineReveal(python, frame, pythonStart)}
					/>
				</div>
			</div>
			<div style={{position: 'absolute', right: MARGIN, top: TOP, ...rise(frame, 2, 12)}}>
				<Wipe before={look.before} after={look.after} t={t} width={IMAGE_W} height={IMAGE_H} />
				<div
					style={{
						display: 'flex',
						justifyContent: 'space-between',
						marginTop: 16,
						fontFamily: fonts.mono,
						fontSize: 21,
						color: colors.faint,
					}}
				>
					<span>{look.photo}</span>
					<span style={{opacity: progress(frame, wipeStart + 30, 14)}}>{look.slug}</span>
				</div>
			</div>
		</div>
	);
};

export const Looks: React.FC = () => (
	<Scene>
		<SectionHeader
			index="05"
			title="Looks"
			subtitle="Recipes adapted from the docs. Each is a few chained calls, or a JSON preset."
		/>
		{looks.map((look, i) => (
			<Sequence key={look.slug} from={STARTS[i]} durationInFrames={timing(look).duration} layout="none">
				<Look look={look} last={i === looks.length - 1} />
			</Sequence>
		))}
	</Scene>
);
