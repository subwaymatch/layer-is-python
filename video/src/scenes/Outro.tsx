import React from 'react';
import {useCurrentFrame} from 'remotion';
import {Code} from '../components/Code';
import {Logo} from '../components/Logo';
import {assembleLogo} from '../components/logoMotion';
import {Scene} from '../components/Scene';
import {colors, fonts, progress, rise} from '../theme';

export const OUTRO_FRAMES = 240;

const LOGO_WIDTH = 230;
const SPEED = 1.5;

export const Outro: React.FC = () => {
	const frame = useCurrentFrame();
	return (
		<Scene>
			<div
				style={{
					position: 'absolute',
					inset: 0,
					display: 'flex',
					flexDirection: 'column',
					alignItems: 'center',
					paddingTop: 196,
				}}
			>
				<Logo width={LOGO_WIDTH} layers={assembleLogo(frame, SPEED)} />
				<div
					style={{
						marginTop: 34,
						fontFamily: fonts.mono,
						fontSize: 76,
						lineHeight: 1.05,
						letterSpacing: '-0.03em',
						color: colors.ink,
						...rise(frame, 34, 12, 26),
					}}
				>
					layeris
				</div>
				<div style={{marginTop: 40, ...rise(frame, 52)}}>
					<Code code="$ pip install layeris" lang="shell" fontSize={30} padding={[16, 28]} />
				</div>
				<div
					style={{
						marginTop: 46,
						display: 'flex',
						flexDirection: 'column',
						alignItems: 'center',
						gap: 8,
						fontFamily: fonts.sans,
						fontSize: 28,
						lineHeight: 1.5,
						color: colors.muted,
					}}
				>
					<span style={rise(frame, 66)}>github.com/subwaymatch/layer-is-python</span>
					<span style={rise(frame, 72)}>subwaymatch.github.io/layer-is-python</span>
				</div>
				<div
					style={{
						marginTop: 34,
						fontFamily: fonts.mono,
						fontSize: 20,
						color: colors.faint,
						opacity: progress(frame, 84, 20),
					}}
				>
					MIT License
				</div>
			</div>
		</Scene>
	);
};
