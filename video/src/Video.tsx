import React from 'react';
import {AbsoluteFill, Audio, Series, interpolate, staticFile} from 'remotion';
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

// Background music from scripts/generate_music.py, generated at the video's
// length. It ends on its own; the short fade only guards the final frames.
// 0.8 brings it from -12.7 to about -14.6 LUFS, with headroom below 0 dBFS.
const MUSIC_VOLUME = 0.8;
const MUSIC_FADE_FRAMES = 15;
const musicVolume = (frame: number) =>
	MUSIC_VOLUME *
	interpolate(frame, [TOTAL_FRAMES - MUSIC_FADE_FRAMES, TOTAL_FRAMES - 1], [1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

export const LayerisVideo: React.FC = () => (
	<AbsoluteFill style={{background: colors.bg}}>
		<Audio src={staticFile('music.mp3')} volume={musicVolume} />
		<Series>
			{SCENES.map(([SceneComponent, frames], i) => (
				<Series.Sequence key={i} durationInFrames={frames}>
					<SceneComponent />
				</Series.Sequence>
			))}
		</Series>
	</AbsoluteFill>
);
