. .venv/bin/activate
export OUT=$(date +%Y-%m-%d).txt
python -u ./gen_my5_cache.py | tee ${OUT}
deactivate
