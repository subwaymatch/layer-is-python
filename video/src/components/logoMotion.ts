import {easeInOut, easeOut, progress} from '../theme';
import type {LayerState} from './Logo';

// Layers start fanned out vertically, like an exploded layer stack, with
// their outlines drawing in. They then settle into place as the fills bloom,
// and the overlap of the translucent fills forms the finished logo.
const SPREAD = [-58, 0, 58];
const STAGGER = 6;

export const LOGO_ASSEMBLY_FRAMES = 92;

export const assembleLogo = (frame: number, speed = 1): LayerState[] => {
	const f = frame * speed;
	return SPREAD.map((spread, i) => {
		const s = i * STAGGER;
		const settle = progress(f, 26 + s, 40, easeInOut);
		return {
			dy: spread * (1 - settle),
			stroke: progress(f, s, 42, easeInOut),
			strokeOpacity: 1 - progress(f, 62, 26),
			fill: progress(f, 30 + s, 40, easeOut),
		};
	});
};
