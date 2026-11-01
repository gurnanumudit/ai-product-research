set -eu
umask 022
mkdir -p /opt/idea19 /opt/idea19/nltk_data
printf '%s\n' '2cf0dbefaa0e656458a71192dea12a86dab74e8c3e3c27a202e38cdd26b2b298  /vercel/sandbox/idea19/worker.py' | sha256sum -c -
python3 -m pip install --disable-pip-version-check --no-cache-dir uv==0.9.5
UV_PYTHON_INSTALL_DIR=/opt/idea19/python python3 -m uv python install 3.9
UV_PYTHON_INSTALL_DIR=/opt/idea19/python python3 -m uv venv --python 3.9 /opt/idea19/venv
cat > /opt/idea19/requirements.build.txt <<'BUILD_PINS'
setuptools==82.0.1
wheel==0.48.0
packaging==26.3
BUILD_PINS
python3 -m uv pip install --python /opt/idea19/venv/bin/python --no-cache --require-hashes --build-constraints /opt/idea19/requirements.build.txt -r /vercel/sandbox/idea19/requirements.txt
/opt/idea19/venv/bin/python - <<'TK_CHECK'
import tkinter
import turtle
interp = tkinter.Tcl()
print('TK_IMPORT_TCL_OK', interp.call('info', 'patchlevel'))
TK_CHECK
/opt/idea19/venv/bin/python -m nltk.downloader -e -d /opt/idea19/nltk_data punkt words stopwords wordnet omw-1.4
ln -s /opt/idea19/nltk_data /usr/share/nltk_data
cp -R /vercel/sandbox/idea19/test_worker.py /vercel/sandbox/idea19/worker.py /vercel/sandbox/idea19/vendor /opt/idea19/
chown -R root:root /opt/idea19
chmod -R a+rX /opt/idea19
# Keep private records inaccessible throughout staging, not just at its end.
install -d -m 700 -o root -g root /opt/idea19/private
for task in /vercel/sandbox/idea19/private/*.json; do
    install -m 600 -o root -g root "$task" /opt/idea19/private/
done
rm -rf /vercel/sandbox/idea19/private
/opt/idea19/venv/bin/python -m pip --version 2>/dev/null || true
python3 -m uv pip freeze --python /opt/idea19/venv/bin/python
