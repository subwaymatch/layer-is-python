import React from 'react';
import {Composition} from 'remotion';
import {FPS, HEIGHT, WIDTH} from './theme';
import {LayerisVideo, TOTAL_FRAMES} from './Video';

export const RemotionRoot: React.FC = () => (
	<Composition
		id="LayerisVideo"
		component={LayerisVideo}
		durationInFrames={TOTAL_FRAMES}
		fps={FPS}
		width={WIDTH}
		height={HEIGHT}
	/>
);
