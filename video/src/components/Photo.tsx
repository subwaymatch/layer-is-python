import React from 'react';
import {Img, staticFile} from 'remotion';
import {colors} from '../theme';

export const Photo: React.FC<{
	src: string;
	width: number;
	height: number;
	style?: React.CSSProperties;
}> = ({src, width, height, style}) => (
	<Img
		src={staticFile(src)}
		style={{
			display: 'block',
			width,
			height,
			objectFit: 'cover',
			borderRadius: 3,
			background: colors.code,
			...style,
		}}
	/>
);

/**
 * `before` with `after` revealed from the left up to `t` (0 to 1), with a thin
 * divider at the edge while the reveal is in progress.
 */
export const Wipe: React.FC<{
	before: string;
	after: string;
	t: number;
	width: number;
	height: number;
	divider?: boolean;
}> = ({before, after, t, width, height, divider = true}) => {
	const x = t * width;
	const showDivider = divider && t > 0 && t < 1;
	return (
		<div style={{position: 'relative', width, height}}>
			<Photo src={before} width={width} height={height} />
			<div
				style={{
					position: 'absolute',
					inset: 0,
					clipPath: `inset(0 ${width - x}px 0 0)`,
				}}
			>
				<Photo src={after} width={width} height={height} />
			</div>
			{showDivider ? (
				<div
					style={{
						position: 'absolute',
						top: 0,
						bottom: 0,
						left: x - 1,
						width: 2,
						background: 'rgba(255,255,255,0.9)',
						boxShadow: '0 0 0 1px rgba(0,0,0,0.06)',
					}}
				/>
			) : null}
		</div>
	);
};
