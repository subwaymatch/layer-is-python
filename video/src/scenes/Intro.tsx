import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {Logo, LOGO_ASPECT} from '../components/Logo';
import {LOGO_ASSEMBLY_FRAMES, assembleLogo} from '../components/logoMotion';
import {Scene} from '../components/Scene';
import {Wordmark} from '../components/Wordmark';
import {colors, easeInOut, fonts, progress, rise} from '../theme';

export const INTRO_FRAMES = 140;

const LOGO_WIDTH = 440;
const SPEED = 2;
// After assembling, the logo shrinks and moves up to sit above the wordmark.
const LIFT_START = Math.ceil(LOGO_ASSEMBLY_FRAMES / SPEED);
const LIFT_FRAMES = 18;
const TYPE_START = LIFT_START + LIFT_FRAMES + 4;

export const Intro: React.FC = () => {
	const frame = useCurrentFrame();
	const lift = progress(frame, LIFT_START, LIFT_FRAMES, easeInOut);
	const scale = interpolate(lift, [0, 1], [1, 0.52]);
	const logoHeight = LOGO_WIDTH * LOGO_ASPECT;
	const logoY = interpolate(lift, [0, 1], [540 - logoHeight / 2, 228]);

	return (
		<Scene>
			<AbsoluteFill>
				<div
					style={{
						position: 'absolute',
						left: 960 - LOGO_WIDTH / 2,
						top: logoY,
						transform: `scale(${scale})`,
						transformOrigin: 'center top',
					}}
				>
					<Logo width={LOGO_WIDTH} layers={assembleLogo(frame, SPEED)} />
				</div>
				<div
					style={{
						position: 'absolute',
						top: 498,
						left: 0,
						right: 0,
						display: 'flex',
						justifyContent: 'center',
					}}
				>
					<Wordmark fontSize={150} frame={frame} start={TYPE_START} />
				</div>
				<p
					style={{
						position: 'absolute',
						top: 718,
						left: 0,
						right: 0,
						margin: 0,
						textAlign: 'center',
						fontFamily: fonts.sans,
						fontSize: 34,
						lineHeight: 1.5,
						color: colors.muted,
						...rise(frame, TYPE_START + 18),
					}}
				>
					Photoshop-style blend modes, adjustments and curves for Python.
				</p>
			</AbsoluteFill>
		</Scene>
	);
};
