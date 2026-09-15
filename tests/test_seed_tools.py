import json
from toolmux_app.seed_tools import validate_dataset

def test_bundled_seed_is_valid():
    rows, errors = validate_dataset()
    assert len(rows) == 500
    assert errors == []

def test_duplicate_slug(tmp_path):
    row={'slug':'same','name':'Same','category':'Extra','repository':'https://github.com/a/b','install':{'method':'git','dependencies':['git'],'repository_name':'b','repository_url':'https://github.com/a/b.git'},'termux':{'status':'experimental'}}
    (tmp_path/'a.json').write_text(json.dumps([row,row]))
    _, errors=validate_dataset(tmp_path)
    assert any('duplicate slug' in e for e in errors)

def test_invalid_record(tmp_path):
    (tmp_path/'a.json').write_text(json.dumps([{'slug':'BAD'}]))
    _, errors=validate_dataset(tmp_path)
    assert errors

def test_filter_and_limit():
    rows, errors=validate_dataset(category='osint',limit=3)
    assert not errors and len(rows)==3
