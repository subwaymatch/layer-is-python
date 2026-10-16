import {Easing, interpolate} from 'remotion';

export const WIDTH = 1920;
export const HEIGHT = 1080;
export const FPS = 30;

// Page gutter shared by every scene.
export const MARGIN = 120;

// Light-theme tokens from docs/assets/site.css.
export const colors = {
	bg: '#ffffff',
	ink: '#1a1b1e',
	muted: '#5f6268',
	faint: '#75777c',
	paren: '#a3a5a9',
	rule: '#e4e4e2',
	code: '#f5f5f3',
	hover: '#ebebe8',
	comment: '#6d7076',
	string: '#2d6a47',
	number: '#a0561b',
	call: '#2a4f8a',
	// Logo gradient edge colour.
	cyan: '#00b9d4',
	// Channel colours for the curves graph.
	red: '#e0474c',
	green: '#30a46c',
	blue: '#3e63dd',
};

export const fonts = {
	sans: '"Schibsted Grotesk", system-ui, sans-serif',
	serif: '"Besley", Georgia, serif',
	mono: '"DM Mono", ui-monospace, Menlo, monospace',
};

export const easeOut = Easing.bezier(0.16, 1, 0.3, 1);
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

/** 0 to 1 over [start, start + duration], clamped and eased. */
export const progress = (
	frame: number,
	start: number,
	duration: number,
	easing: (t: number) => number = easeOut,
) =>
	interpolate(frame, [start, start + duration], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing,
	});

/** Fade in while rising a few pixels: the default entrance for text. */
export const rise = (frame: number, start: number, distance = 14, duration = 22) => {
	const t = progress(frame, start, duration);
	return {opacity: t, transform: `translateY(${(1 - t) * distance}px)`};
};
