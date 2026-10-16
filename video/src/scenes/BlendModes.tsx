import React from 'react';
import {useCurrentFrame} from 'remotion';
import {Photo, Wipe} from '../components/Photo';
import {Scene} from '../components/Scene';
import {SectionHeader} from '../components/SectionHeader';
import assets from '../data/assets.json';
import {MARGIN, colors, easeInOut, fonts, progress, rise} from '../theme';

const {blend} = assets;

const COLS = 5;
const TILE_W = 312;
const TILE_H = 208;
const GAP_X = (1920 - 2 * MARGIN - COLS * TILE_W) / (COLS - 1);
const GAP_Y = 24;
const GRID_TOP = 300;

const TILES_IN = 26;
const APPLY_START = 62;
const APPLY_EVERY = 9;
const WIPE_FRAMES = 22;

export const BLEND_FRAMES = 300;

const Swatch: React.FC = () => (
	<span
		style={{
			display: 'inline-block',
			width: 22,
			height: 22,
			margin: '0 8px -3px 2px',
			borderRadius: 2,
			background: blend.color,
		}}
	/>
);

export const BlendModes: React.FC = () => {
	const frame = useCurrentFrame();
	return (
		<Scene>
			<SectionHeader
				index="03"
				title="Blend modes"
				subtitle={
					<>
						Each tile blends <Swatch />
						<span style={{fontFamily: fonts.mono, fontSize: 25, color: colors.ink}}>
							"{blend.color}"
						</span>{' '}
						over the photo. The blend layer can also be a NumPy array.
					</>
				}
			/>
			{blend.tiles.map((tile, k) => {
				const col = k % COLS;
				const row = Math.floor(k / COLS);
				const applyAt = APPLY_START + (k - 1) * APPLY_EVERY;
				const t = k === 0 ? 1 : progress(frame, applyAt, WIPE_FRAMES, easeInOut);
				const labelIn = k === 0 ? progress(frame, TILES_IN + 10, 14) : progress(frame, applyAt + 6, 14);
				return (
					<div
						key={tile.mode}
						style={{
							position: 'absolute',
							left: MARGIN + col * (TILE_W + GAP_X),
							top: GRID_TOP + row * (TILE_H + GAP_Y),
							...rise(frame, TILES_IN + k * 2, 12, 18),
						}}
					>
						{k === 0 || t >= 1 ? (
							<Photo src={tile.image} width={TILE_W} height={TILE_H} />
						) : (
							<Wipe before={blend.tiles[0].image} after={tile.image} t={t} width={TILE_W} height={TILE_H} />
						)}
						<div
							style={{
								position: 'absolute',
								left: 10,
								bottom: 10,
								padding: '3px 9px 4px',
								borderRadius: 2,
								background: 'rgba(255,255,255,0.94)',
								fontFamily: fonts.mono,
								fontSize: 19,
								color: k === 0 ? colors.muted : colors.ink,
								opacity: labelIn,
							}}
						>
							{tile.mode}
						</div>
					</div>
				);
			})}
		</Scene>
	);
};
