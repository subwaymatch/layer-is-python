import React from 'react';
import {AbsoluteFill, Audio, Sequence, Series, interpolate, staticFile} from 'remotion';
import {EXIT_FRAMES} from './components/Scene';
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

// The logo's sound effect (scripts/generate_sound_effect.py) plays as its
// outlines start to draw.
const LOGO_SOUND_START = 3;

// The music (scripts/generate_music.py) starts as the logo fades out at the
// end of the intro, and fades over the last second so it ends with the video.
const MUSIC_START = INTRO_FRAMES - EXIT_FRAMES;
const MUSIC_FRAMES = TOTAL_FRAMES - MUSIC_START;
const MUSIC_FADE_FRAMES = 30;
const musicVolume = (frame: number) =>
	interpolate(frame, [MUSIC_FRAMES - MUSIC_FADE_FRAMES, MUSIC_FRAMES - 1], [1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

export const LayerisVideo: React.FC = () => (
	<AbsoluteFill style={{background: colors.bg}}>
		<Sequence from={LOGO_SOUND_START} layout="none">
			<Audio src={staticFile('logo.mp3')} />
		</Sequence>
		<Sequence from={MUSIC_START} layout="none">
			<Audio src={staticFile('music.mp3')} volume={musicVolume} />
		</Sequence>
		<Series>
			{SCENES.map(([SceneComponent, frames], i) => (
				<Series.Sequence key={i} durationInFrames={frames}>
					<SceneComponent />
				</Series.Sequence>
			))}
		</Series>
	</AbsoluteFill>
);
