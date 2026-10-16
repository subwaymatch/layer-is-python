import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Code, caretBlink, typeLines} from '../components/Code';
import {Photo, Wipe} from '../components/Photo';
import {Scene} from '../components/Scene';
import {SectionHeader} from '../components/SectionHeader';
import assets from '../data/assets.json';
import {MARGIN, colors, easeInOut, fonts, progress, rise} from '../theme';

const {chain} = assets;

const CODE = [
	'from layeris import LayerImage',
	'',
	`image = LayerImage.from_file("${chain.photo}")`,
	...chain.steps.map((step, i) => (i === 0 ? `(image.${step}` : `      .${step}`)),
	`      .save("${chain.saveAs}"))`,
].join('\n');

const FIRST_STEP_LINE = 3;
const SAVE_LINE = FIRST_STEP_LINE + chain.steps.length;

const CODE_IN = 12;
const IMAGE_IN = 50;
const STEP_START = 72;
const STEP_EVERY = 52;
const TYPE_FRAMES = 18;
const WIPE_FRAMES = 24;
const CPF = 2.6; // characters typed per frame

const stepStart = (k: number) => STEP_START + k * STEP_EVERY;
const applyAt = (k: number) => stepStart(k) + TYPE_FRAMES;
const SAVE_AT = stepStart(chain.steps.length);

export const CHAIN_FRAMES = SAVE_AT + 50;

const IMAGE_W = 840;
const IMAGE_H = 560;

export const Chain: React.FC = () => {
	const frame = useCurrentFrame();

	const starts: (number | undefined)[] = [CODE_IN + 6, undefined, CODE_IN + 22];
	chain.steps.forEach((_, k) => starts.push(stepStart(k)));
	starts.push(SAVE_AT);
	const reveal = typeLines(CODE, frame, starts, CPF);

	// The line being typed carries the caret.
	let caretLine = 0;
	starts.forEach((s, i) => {
		if (s !== undefined && frame >= s) caretLine = i;
	});
	const lastTyped = SAVE_AT + 12;

	// Which step's result is showing, and how far the next one has wiped in.
	let shown = 0;
	let wipe = 0;
	chain.steps.forEach((_, k) => {
		const t = progress(frame, applyAt(k), WIPE_FRAMES, easeInOut);
		if (t >= 1) shown = k + 1;
		else if (t > 0) wipe = t;
	});

	// Tint the most recently applied line until the next one applies.
	let highlight: {line: number; opacity: number} | undefined;
	chain.steps.forEach((_, k) => {
		if (frame >= applyAt(k)) {
			highlight = {line: FIRST_STEP_LINE + k, opacity: progress(frame, applyAt(k), 8)};
		}
	});
	if (frame >= SAVE_AT + 14) {
		highlight = {line: SAVE_LINE, opacity: progress(frame, SAVE_AT + 14, 8)};
	}

	let caption = chain.photo;
	if (shown > 0 || wipe > 0) {
		const k = wipe > 0 ? shown : shown - 1;
		caption = `.${chain.steps[k]}`;
	}
	if (frame >= SAVE_AT + 14) caption = `saved ${chain.saveAs}`;

	const imageIn = progress(frame, IMAGE_IN, 16);

	return (
		<Scene>
			<SectionHeader
				index="02"
				title="Chain operations"
				subtitle="Every operation returns the image, so a whole edit reads as one pipeline."
			/>
			<div style={{position: 'absolute', left: MARGIN, top: 330, ...rise(frame, CODE_IN)}}>
				<Code
					code={CODE}
					fontSize={26}
					width={770}
					padding={[30, 36]}
					reveal={reveal}
					highlight={highlight}
					caret={frame < lastTyped + 30 ? {line: caretLine, opacity: caretBlink(frame, lastTyped)} : undefined}
				/>
			</div>
			<div
				style={{
					position: 'absolute',
					right: MARGIN,
					top: 330,
					width: IMAGE_W,
					opacity: imageIn,
					transform: `translateY(${interpolate(imageIn, [0, 1], [16, 0])}px)`,
				}}
			>
				{wipe > 0 ? (
					<Wipe
						before={chain.images[shown]}
						after={chain.images[shown + 1]}
						t={wipe}
						width={IMAGE_W}
						height={IMAGE_H}
					/>
				) : (
					<Photo src={chain.images[shown]} width={IMAGE_W} height={IMAGE_H} />
				)}
				<div
					style={{
						marginTop: 18,
						fontFamily: fonts.mono,
						fontSize: 22,
						color: colors.faint,
					}}
				>
					{caption}
				</div>
			</div>
		</Scene>
	);
};
