import React from 'react';
import {useCurrentFrame} from 'remotion';
import {Code, caretBlink, typeLines} from '../components/Code';
import {Scene} from '../components/Scene';
import {SectionHeader} from '../components/SectionHeader';
import {MARGIN, rise} from '../theme';

export const INSTALL_FRAMES = 120;

const PYPI = '$ pip install layeris\nSuccessfully installed layeris-0.4.0';

const PYPI_START = 22;
const PYPI_OUTPUT = PYPI_START + 34;

export const Install: React.FC = () => {
	const frame = useCurrentFrame();
	// `pip install` types, then its output appears in one go.
	const reveal = [
		typeLines(PYPI, frame, [PYPI_START + 8], 1.2)[0],
		frame >= PYPI_OUTPUT ? Infinity : 0,
	];

	return (
		<Scene>
			<SectionHeader
				index="01"
				title="Install"
				subtitle="Python 3.10 or higher. The only dependencies are NumPy, Pillow and Requests."
			/>
			<div style={{position: 'absolute', left: MARGIN, top: 330, ...rise(frame, PYPI_START)}}>
				<Code
					code={PYPI}
					lang="shell"
					fontSize={32}
					padding={[30, 40]}
					reveal={reveal}
					caret={frame < PYPI_OUTPUT ? {line: 0, opacity: caretBlink(frame, PYPI_OUTPUT)} : undefined}
				/>
			</div>
		</Scene>
	);
};
