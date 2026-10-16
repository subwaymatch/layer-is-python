import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from 'remotion';
import {Code, caretBlink, typeLines} from '../components/Code';
import {Photo} from '../components/Photo';
import {Scene} from '../components/Scene';
import {SectionHeader} from '../components/SectionHeader';
import assets from '../data/assets.json';
import {MARGIN, colors, easeInOut, fonts, progress, rise} from '../theme';

const {curves} = assets;

const IMAGE_W = 960;
const IMAGE_H = 640;
const TOP = 300;
const COL_X = 1920 - MARGIN - 640;
const GRAPH = 420;
const GRAPH_TOP = TOP + 50;

const CHANNEL_COLORS: Record<string, string> = {r: colors.red, g: colors.green, b: colors.blue};

const IN = 14;
const PHASE_FRAMES = 66;
// Per phase: when its code line starts typing, and when its points start moving.
const PHASES = curves.phases.map((_, i) => {
	const type = 30 + i * 100;
	return {type, move: type + 22};
});
const LAST_TYPED = PHASES[PHASES.length - 1].type + 22;

export const CURVES_FRAMES = PHASES[PHASES.length - 1].move + PHASE_FRAMES + 40;

const lerp = (a: number[], b: number[], t: number) => a.map((x, i) => x + (b[i] - x) * t);

const fmt = (points: number[]) => `[${points.map((v) => v.toFixed(2)).join(', ')}]`;

export const Curves: React.FC = () => {
	const frame = useCurrentFrame();
	const t = curves.phases.map((_, i) => progress(frame, PHASES[i].move, PHASE_FRAMES, easeInOut));
	const points = curves.phases.map((p, i) => lerp(p.start, p.target, t[i]));

	const code = curves.phases
		.map((p, i) => `image.curve("${p.channels}", ${fmt(points[i])})`)
		.join('\n');
	const reveal = typeLines(code, frame, PHASES.map((p) => p.type), 2.6);
	const caretLine = frame >= PHASES[1]?.type ? 1 : 0;

	// The image for the furthest phase that has started, crossfading between
	// the two renders either side of the current point positions.
	let phase = 0;
	PHASES.forEach((p, i) => {
		if (frame >= p.move) phase = i;
	});
	const images = curves.phases[phase].images;
	const pos = t[phase] * (images.length - 1);
	const lo = Math.floor(pos);
	const hi = Math.min(images.length - 1, lo + 1);
	const mix = pos - lo;

	const toX = (x: number) => x * GRAPH;
	const toY = (y: number) => GRAPH - y * GRAPH;

	return (
		<Scene>
			<SectionHeader
				index="04"
				title="Curves"
				subtitle="Remap tones on any of the R, G and B channels, through evenly spaced control points."
			/>
			<div style={{position: 'absolute', left: MARGIN, top: TOP, ...rise(frame, IN)}}>
				<div style={{position: 'relative', width: IMAGE_W, height: IMAGE_H}}>
					<Photo src={images[lo]} width={IMAGE_W} height={IMAGE_H} />
					{mix > 0 ? (
						<AbsoluteFill style={{opacity: mix}}>
							<Img
								src={staticFile(images[hi])}
								style={{width: IMAGE_W, height: IMAGE_H, borderRadius: 3, display: 'block'}}
							/>
						</AbsoluteFill>
					) : null}
				</div>
			</div>

			<div style={{position: 'absolute', left: COL_X + 30, top: TOP, ...rise(frame, IN + 6)}}>
				<div style={{display: 'flex', gap: 28, height: 30, fontFamily: fonts.mono, fontSize: 19, color: colors.muted}}>
					{curves.phases.map((p, i) => (
						<span key={p.channels} style={{display: 'flex', alignItems: 'center', gap: 10, opacity: progress(frame, PHASES[i].type, 12)}}>
							<span style={{width: 26, height: 3, background: CHANNEL_COLORS[p.channels[0]]}} />
							{p.channels}
						</span>
					))}
				</div>
			</div>

			<svg
				width={GRAPH}
				height={GRAPH}
				style={{position: 'absolute', left: COL_X + 30, top: GRAPH_TOP, overflow: 'visible', ...rise(frame, IN + 6)}}
			>
				{[0.25, 0.5, 0.75].map((g) => (
					<g key={g} stroke={colors.rule} strokeWidth={1}>
						<line x1={toX(g)} y1={0} x2={toX(g)} y2={GRAPH} />
						<line x1={0} y1={toY(g)} x2={GRAPH} y2={toY(g)} />
					</g>
				))}
				<rect x={0} y={0} width={GRAPH} height={GRAPH} fill="none" stroke={colors.paren} strokeWidth={1} />
				<line x1={0} y1={GRAPH} x2={GRAPH} y2={0} stroke={colors.paren} strokeWidth={1.2} strokeDasharray="5 6" />
				{curves.phases.map((p, i) => {
					const visible = progress(frame, PHASES[i].type, 12);
					const pts = points[i].map((y, j) => [toX(j / (points[i].length - 1)), toY(y)]);
					const color = CHANNEL_COLORS[p.channels[0]];
					const active = frame >= PHASES[i].type && (i === PHASES.length - 1 || frame < PHASES[i + 1].type);
					return (
						<g key={p.channels} opacity={visible}>
							<polyline
								points={pts.map(([x, y]) => `${x},${y}`).join(' ')}
								fill="none"
								stroke={color}
								strokeWidth={3}
								strokeLinejoin="round"
							/>
							{pts.map(([x, y], j) => (
								<circle
									key={j}
									cx={x}
									cy={y}
									r={active ? 7 : 5}
									fill={active ? colors.bg : color}
									stroke={color}
									strokeWidth={2.5}
								/>
							))}
						</g>
					);
				})}
				<text x={-14} y={GRAPH + 6} textAnchor="end" fontFamily={fonts.mono} fontSize={17} fill={colors.faint}>
					0
				</text>
				<text x={-14} y={8} textAnchor="end" fontFamily={fonts.mono} fontSize={17} fill={colors.faint}>
					1
				</text>
				<text x={GRAPH} y={GRAPH + 26} textAnchor="middle" fontFamily={fonts.mono} fontSize={17} fill={colors.faint}>
					1
				</text>
			</svg>

			<div style={{position: 'absolute', left: COL_X, top: TOP + IMAGE_H - 108, ...rise(frame, PHASES[0].type - 6)}}>
				<Code
					code={code}
					fontSize={20}
					width={640}
					padding={[20, 20]}
					reveal={reveal}
					caret={frame < LAST_TYPED + 40 ? {line: caretLine, opacity: caretBlink(frame, LAST_TYPED)} : undefined}
				/>
			</div>
		</Scene>
	);
};
