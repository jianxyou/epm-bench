#!/bin/bash
# Install habitat-sim (osx-64 under Rosetta) + test scenes. Fail-soft, verbose.
set -x
cd "$(dirname "$0")"
MF=$HOME/miniforge3-x86
if [ ! -d "$MF" ]; then
  curl -sL https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh -o /tmp/mf.sh || exit 1
  bash /tmp/mf.sh -b -p "$MF" || exit 1
fi
source "$MF/bin/activate"
if ! conda env list | grep -q "^habitat "; then
  CONDA_SUBDIR=osx-64 conda create -y -n habitat python=3.9 || exit 1
fi
conda activate habitat
conda config --env --set subdir osx-64
conda install -y -c aihabitat -c conda-forge habitat-sim || {
  echo "latest failed, trying 0.2.2"; conda install -y -c aihabitat -c conda-forge habitat-sim=0.2.2 || exit 1; }
python -c "import habitat_sim; print('HABITAT_SIM_OK', habitat_sim.__version__)" || exit 1
mkdir -p data
python -m habitat_sim.utils.datasets_download --uids habitat_test_scenes --data-path data/ --no-replace || true
ls -la data/scene_datasets/habitat-test-scenes/ 2>/dev/null || find data -name "*.glb" | head
echo HABITAT_INSTALL_DONE
