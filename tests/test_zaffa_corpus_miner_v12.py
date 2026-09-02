from pathlib import Path
import tempfile
import json
from scripts.run_zaffa_corpus_miner_v12 import normalize_arabic, group_words, load_v11

def test_normalize_arabic():
    assert normalize_arabic("الضُّوئِيّ") == "الضوئي"

def test_group_words():
    words = [{"start":0,"end":2},{"start":2.1,"end":4}]
    assert len(group_words(words, 4.1, 1.0)) == 1
    assert len(group_words(words, 3.0, 1.0)) == 2

def test_load_v11(tmp_path: Path):
    p=tmp_path/"master.tsv"
    p.write_text("ID\tSESSION\tPATTERN\tWORD\tTASHKEEL\tPHONES\tTARGETS\n0001\tS01\tA\tالضوئي\tالضُّوئِيّ\taa D D a w < ii y i\taa,ii,w,y,<,D\n",encoding="utf-8")
    words, phones=load_v11(p)
    assert "الضوئي" in words
    assert phones["aa"] == 1
