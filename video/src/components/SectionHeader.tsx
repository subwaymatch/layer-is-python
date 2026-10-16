import React from 'react';
import {useCurrentFrame} from 'remotion';
import {MARGIN, colors, easeInOut, fonts, progress, rise} from '../theme';

export const HEADER_TOP = 84;

/** Mirrors the docs' section headings: a full-width rule, then a serif title. */
export const SectionHeader: React.FC<{
	index: string;
	title: string;
	subtitle?: React.ReactNode;
	start?: number;
}> = ({index, title, subtitle, start = 0}) => {
	const frame = useCurrentFrame() - start;
	const rule = progress(frame, 0, 30, easeInOut);
	return (
		<div style={{position: 'absolute', left: MARGIN, right: MARGIN, top: HEADER_TOP}}>
			<div
				style={{
					height: 1.5,
					background: colors.ink,
					transformOrigin: 'left center',
					transform: `scaleX(${rule})`,
				}}
			/>
			<div
				style={{
					display: 'flex',
					justifyContent: 'space-between',
					alignItems: 'baseline',
					marginTop: 26,
				}}
			>
				<h2
					style={{
						margin: 0,
						fontFamily: fonts.serif,
						fontWeight: 500,
						fontSize: 54,
						lineHeight: 1.15,
						letterSpacing: '-0.01em',
						color: colors.ink,
						...rise(frame, 6),
					}}
				>
					{title}
				</h2>
				<span
					style={{
						fontFamily: fonts.mono,
						fontSize: 22,
						color: colors.faint,
						...rise(frame, 10),
					}}
				>
					{index}
				</span>
			</div>
			{subtitle ? (
				<p
					style={{
						margin: '14px 0 0',
						maxWidth: 1240,
						fontFamily: fonts.sans,
						fontSize: 27,
						lineHeight: 1.5,
						color: colors.muted,
						...rise(frame, 14),
					}}
				>
					{subtitle}
				</p>
			) : null}
		</div>
	);
};
