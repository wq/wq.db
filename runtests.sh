set -e
if [ "$LINT" ]; then
    flake8 rest patterns tests --exclude migrations
    flake8 */*/migrations --ignore E501
else
    python setup.py test
fi
