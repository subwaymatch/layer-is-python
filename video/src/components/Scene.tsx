import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, easeInOut, progress} from '../theme';

export const EXIT_FRAMES = 10;

/** A white page whose content fades out over the scene's last frames. */
export const Scene: React.FC<{
	children: React.ReactNode;
	exit?: boolean;
	exitFrames?: number;
}> = ({children, exit = true, exitFrames = EXIT_FRAMES}) => {
	const frame = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();
	const out = exit ? progress(frame, durationInFrames - exitFrames, exitFrames, easeInOut) : 0;
	return (
		<AbsoluteFill style={{background: colors.bg}}>
			<AbsoluteFill style={{opacity: 1 - out, transform: `translateY(${-8 * out}px)`}}>
				{children}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
