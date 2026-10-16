import React from 'react';
import {AbsoluteFill, Series} from 'remotion';
import './fonts';
import {BLEND_FRAMES, BlendModes} from './scenes/BlendModes';
import {CHAIN_FRAMES, Chain} from './scenes/Chain';
import {CURVES_FRAMES, Curves} from './scenes/Curves';
import {INSTALL_FRAMES, Install} from './scenes/Install';
import {INTRO_FRAMES, Intro} from './scenes/Intro';
import {LOOKS_FRAMES, Looks} from './scenes/Looks';
import {OUTRO_FRAMES, Outro} from './scenes/Outro';
import {colors} from './theme';

const SCENES: [React.FC, number][] = [
	[Intro, INTRO_FRAMES],
	[Install, INSTALL_FRAMES],
	[Chain, CHAIN_FRAMES],
	[BlendModes, BLEND_FRAMES],
	[Curves, CURVES_FRAMES],
	[Looks, LOOKS_FRAMES],
	[Outro, OUTRO_FRAMES],
];

export const TOTAL_FRAMES = SCENES.reduce((sum, [, frames]) => sum + frames, 0);

export const LayerisVideo: React.FC = () => (
	<AbsoluteFill style={{background: colors.bg}}>
		<Series>
			{SCENES.map(([SceneComponent, frames], i) => (
				<Series.Sequence key={i} durationInFrames={frames}>
					<SceneComponent />
				</Series.Sequence>
			))}
		</Series>
	</AbsoluteFill>
);
