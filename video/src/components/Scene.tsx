import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {colors, easeInOut, progress} from '../theme';

export const EXIT_FRAMES = 14;

/** A white page whose content fades out over the scene's last frames. */
export const Scene: React.FC<{children: React.ReactNode; exit?: boolean}> = ({
	children,
	exit = true,
}) => {
	const frame = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();
	const out = exit ? progress(frame, durationInFrames - EXIT_FRAMES, EXIT_FRAMES, easeInOut) : 0;
	return (
		<AbsoluteFill style={{background: colors.bg}}>
			<AbsoluteFill style={{opacity: 1 - out, transform: `translateY(${-8 * out}px)`}}>
				{children}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
