import React from 'react';
import {Sequence, useCurrentFrame} from 'remotion';
import {Code} from '../components/Code';
import {Photo, Wipe} from '../components/Photo';
import {EXIT_FRAMES, Scene} from '../components/Scene';
import {SectionHeader} from '../components/SectionHeader';
import assets from '../data/assets.json';
import {MARGIN, colors, easeInOut, fonts, progress, rise} from '../theme';

const {looks} = assets;

type LookData = (typeof looks)[number];

const FIRST_DELAY = 12;
const WIPE_FRAMES = 32;
const HOLD_FRAMES = 42;
// The next look's photo fades in over the previous result for this long.
const SWAP_FRAMES = 10;

const IMAGE_W = 840;
const IMAGE_H = 560;
const TOP = 318;

const pythonCode = (look: LookData) =>
	`image = LayerImage.from_file("${look.photo}")\n${look.code}`;

/** When each part of a look appears, in frames from the look's start. */
const timing = (look: LookData, last: boolean) => {
	const codeStart = 6;
	const presetLines = look.preset ? look.preset.split('\n').length : 0;
	const pythonStart = codeStart + (look.preset ? presetLines * 2 + 6 : 0);
	const wipeStart = pythonStart + pythonCode(look).split('\n').length * 3 + 10;
	// The last look also covers the scene's fade out.
	const duration = wipeStart + WIPE_FRAMES + HOLD_FRAMES + (last ? EXIT_FRAMES : 0);
	return {codeStart, pythonStart, wipeStart, duration};
};

const isLast = (i: number) => i === looks.length - 1;

const STARTS = looks.reduce<number[]>(
	(acc, _look, i) => [...acc, i === 0 ? FIRST_DELAY : acc[i - 1] + timing(looks[i - 1], false).duration],
	[],
);

export const LOOKS_FRAMES = STARTS[looks.length - 1] + timing(looks[looks.length - 1], true).duration;

/** Lines appear one after another rather than being typed. */
const lineReveal = (code: string, frame: number, start: number, every = 3) =>
	code.split('\n').map((_, i) => (frame >= start + i * every ? Infinity : 0));

/**
 * One look. Looks follow each other without a fade out: the text swaps
 * straight away and the new photo fades in over `previous`, the last result.
 */
const Look: React.FC<{look: LookData; last: boolean; previous?: string}> = ({
	look,
	last,
	previous,
}) => {
	const frame = useCurrentFrame();
	const {codeStart, pythonStart, wipeStart} = timing(look, last);
	const python = pythonCode(look);
	const presetName = `${look.slug}.json`;
	const t = progress(frame, wipeStart, WIPE_FRAMES, easeInOut);
	const textIn = (start: number) => rise(frame, start, previous ? 8 : 14, previous ? 10 : 22);

	return (
		<div style={{position: 'absolute', inset: 0}}>
			<div style={{position: 'absolute', left: MARGIN, top: TOP, width: 770}}>
				<h3
					style={{
						margin: '0 0 22px',
						fontFamily: fonts.sans,
						fontWeight: 600,
						fontSize: 34,
						color: colors.ink,
						...textIn(0),
					}}
				>
					{look.title}
				</h3>
				{look.preset ? (
					<div style={{marginBottom: 22, ...textIn(codeStart - 4)}}>
						<div style={{fontFamily: fonts.mono, fontSize: 19, color: colors.muted, marginBottom: 10}}>
							{presetName}
						</div>
						<Code
							code={look.preset}
							lang="json"
							fontSize={17}
							lineHeight={1.75}
							padding={[18, 22]}
							reveal={lineReveal(look.preset, frame, codeStart, 2)}
						/>
					</div>
				) : null}
				<div style={textIn(pythonStart - 4)}>
					<Code
						code={python}
						fontSize={look.preset ? 20 : 22}
						padding={look.preset ? [18, 22] : [26, 30]}
						reveal={lineReveal(python, frame, pythonStart)}
					/>
				</div>
			</div>
			<div style={{position: 'absolute', right: MARGIN, top: TOP, ...(previous ? {} : rise(frame, 2, 12))}}>
				<div style={{position: 'relative', width: IMAGE_W, height: IMAGE_H}}>
					{previous ? <Photo src={previous} width={IMAGE_W} height={IMAGE_H} style={{position: 'absolute'}} /> : null}
					<div style={{position: 'absolute', inset: 0, opacity: previous ? progress(frame, 0, SWAP_FRAMES) : 1}}>
						<Wipe before={look.before} after={look.after} t={t} width={IMAGE_W} height={IMAGE_H} />
					</div>
				</div>
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
					<span style={{opacity: progress(frame, wipeStart + 22, 10)}}>{look.slug}</span>
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
			<Sequence key={look.slug} from={STARTS[i]} durationInFrames={timing(look, isLast(i)).duration} layout="none">
				<Look look={look} last={isLast(i)} previous={looks[i - 1]?.after} />
			</Sequence>
		))}
	</Scene>
);
