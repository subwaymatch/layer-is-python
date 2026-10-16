// The same three families as the docs site, bundled locally so renders never
// depend on network access.
import '@fontsource/dm-mono/400.css';
import '@fontsource/dm-mono/500.css';
import '@fontsource/schibsted-grotesk/400.css';
import '@fontsource/schibsted-grotesk/500.css';
import '@fontsource/schibsted-grotesk/600.css';
import '@fontsource/besley/500.css';
import {continueRender, delayRender} from 'remotion';

const FACES = [
	'400 16px "DM Mono"',
	'500 16px "DM Mono"',
	'400 16px "Schibsted Grotesk"',
	'500 16px "Schibsted Grotesk"',
	'600 16px "Schibsted Grotesk"',
	'500 16px "Besley"',
];

const handle = delayRender('Loading fonts');
Promise.all(FACES.map((face) => document.fonts.load(face)))
	.then(() => continueRender(handle))
	.catch((err) => {
		console.error(err);
		continueRender(handle);
	});
