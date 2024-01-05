from setuptools import setup, find_packages

setup(
    name='modelforge',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=open('requirements.txt').read().splitlines(),
    entry_points={'console_scripts': ['modelforge=modelforge.main:main']},
    author='Brandon Dalton',
    author_email='brandon7cc@gmail.com',
    description=
    'Evaluate hosted OpenAI GPT / Google PaLM2/Gemini or local Ollama models against a task',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Brandon7CC/MODELFORGE',
    license='MIT')
