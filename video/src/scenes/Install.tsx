import React from 'react';
import {useCurrentFrame} from 'remotion';
import {Code, caretBlink, typeLines} from '../components/Code';
import {Scene} from '../components/Scene';
import {SectionHeader} from '../components/SectionHeader';
import {MARGIN, colors, fonts, rise} from '../theme';

export const INSTALL_FRAMES = 165;

const PYPI = '$ pip install layeris\nSuccessfully installed layeris-0.4.0';
const SOURCE = [
	'$ git clone https://github.com/subwaymatch/layer-is-python.git',
	'$ cd layer-is-python',
	'$ pip install -e .',
].join('\n');

const PYPI_START = 26;
const PYPI_OUTPUT = PYPI_START + 34;
const SOURCE_START = 70;

const Label: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({
	children,
	style,
}) => (
	<h3
		style={{
			margin: '0 0 18px',
			fontFamily: fonts.sans,
			fontWeight: 600,
			fontSize: 28,
			color: colors.ink,
			...style,
		}}
	>
		{children}
	</h3>
);

export const Install: React.FC = () => {
	const frame = useCurrentFrame();
	// `pip install` types, then its output appears in one go.
	const pypiTyped = [
		typeLines(PYPI, frame, [PYPI_START + 8], 1.2)[0],
		frame >= PYPI_OUTPUT ? Infinity : 0,
	];
	const sourceTyped = typeLines(SOURCE, frame, [SOURCE_START + 8, SOURCE_START + 44, SOURCE_START + 58], 2.4);
	const sourceEnd = SOURCE_START + 66;

	return (
		<Scene>
			<SectionHeader
				index="01"
				title="Install"
				subtitle="Python 3.10 or higher. The only dependencies are NumPy, Pillow and Requests."
			/>
			<div
				style={{
					position: 'absolute',
					left: MARGIN,
					right: MARGIN,
					top: 330,
					display: 'flex',
					gap: 64,
				}}
			>
				<div style={{flex: '0 0 700px', ...rise(frame, PYPI_START)}}>
					<Label>From PyPI</Label>
					<Code
						code={PYPI}
						lang="shell"
						fontSize={28}
						reveal={pypiTyped}
						caret={frame < PYPI_OUTPUT ? {line: 0, opacity: caretBlink(frame, PYPI_OUTPUT)} : undefined}
					/>
				</div>
				<div style={{flex: '1 1 auto', minWidth: 0, ...rise(frame, SOURCE_START)}}>
					<Label>From source</Label>
					<Code
						code={SOURCE}
						lang="shell"
						fontSize={21}
						lineHeight={1.75}
						reveal={sourceTyped}
						caret={
							frame < sourceEnd + 40
								? {
										line: frame < SOURCE_START + 44 ? 0 : frame < SOURCE_START + 58 ? 1 : 2,
										opacity: caretBlink(frame, sourceEnd),
									}
								: undefined
						}
					/>
				</div>
			</div>
		</Scene>
	);
};
