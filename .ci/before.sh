apt-get update

git clone --depth=1 https://gitlab.com/kaitaiStructCompile.py/kaitaiStructCompile.py.git
export KSCP=./kaitaiStructCompile.py
source $KSCP/.ci/before.sh
pip install --upgrade $KSCP

source ./.ci/pythonStdlibFixes.sh
pip3 install coveralls git+https://github.com/berkerpeksag/astor.git xgboost git+https://gitlab.com/KOLANICH/alternativez.py.git git+https://github.com/kaitai-io/kaitai_struct_python_runtime.git
