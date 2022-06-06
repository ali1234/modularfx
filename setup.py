from setuptools import setup

setup(
    name='modularfx',
    version='0.1',
    packages=[
        'modularfx',
        'modularfx.gui',
        'modularfx.node',
    ],
    package_data={
        'modularfx': [
            'data/icons/*',
            'data/examples/*',
        ],
    },
    entry_points={
        'console_scripts': [
            'modularfx=modularfx.main:main',
        ]
    },
    install_requires=['gensound', 'pygame', 'nodeeditor', 'QtPy', 'PyQt5', 'click', 'pyqtconsole'],
    url='https://github.com/ali1234/modularfx',
    license='GPL',
    author='Alistair Buxton',
    author_email='a.j.buxton@gmail.com',
    description='Modular synthesizer.'
)
